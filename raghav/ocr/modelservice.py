# model_service.py
#
# Plain Python integration layer — no Flask, no HTTP, no assumptions
# about what kind of frontend is calling it. Whether the frontend ends
# up being Streamlit, Tkinter, PyQt, a Jupyter notebook, or a web API
# later, it just does:
#
#   import model_service as ms
#   result = ms.identify_from_image("path/to/photo.jpg")
#
# KEY DESIGN — SINGLETON MODEL LOADING:
#   EasyOCR, the DrugBank search index, and the RDKit fingerprint
#   database are all expensive to build. `ModelService` loads each one
#   lazily, the first time it's actually needed, and caches it as a
#   class attribute. Because Python only ever imports a module once
#   per process (re-importing just returns the cached module object),
#   every part of the frontend that does `import model_service` is
#   sharing the exact same loaded models — nothing is ever loaded twice,
#   no matter how many times these functions are called.

import os
import threading

from config import SUPPORTED_FORMATS, MAX_IMAGE_MB, OCR_CONFIDENCE
from image_utils import validate_image, convert_to_jpg, preprocess
from drug_matcher import load_drugbank, build_index, match_drug
from interaction import load_interactions, check_interaction
from tanimoto_match import load_drugbank_with_fingerprints, find_similar_drugs


# ────────────────────────────────────────────────────────────
#  SINGLETON MODEL LOADER
# ────────────────────────────────────────────────────────────
class ModelService:
    """
    Holds every heavy object the app needs and loads each one
    lazily, exactly once, no matter how many times these methods
    are called or from how many places in the frontend.

    Pattern used (double-checked locking):
      1. Check if already loaded (fast, no lock) — the common case.
      2. If not, acquire a lock and check again before loading, so
         two calls arriving at the same instant (e.g. from two UI
         threads) can't both trigger a duplicate load.
    """
    _lock = threading.Lock()

    _drugbank_df  = None
    _drug_index   = None
    _interactions = None
    _fingerprints = None
    _ocr_reader   = None

    @classmethod
    def get_drug_index(cls):
        if cls._drug_index is None:
            with cls._lock:
                if cls._drug_index is None:
                    print(" [ModelService] Loading DrugBank + building index...")
                    cls._drugbank_df = load_drugbank()
                    cls._drug_index = build_index(cls._drugbank_df)
        return cls._drug_index

    @classmethod
    def get_interactions(cls):
        if cls._interactions is None:
            with cls._lock:
                if cls._interactions is None:
                    print(" [ModelService] Loading interactions table...")
                    cls._interactions = load_interactions()
        return cls._interactions

    @classmethod
    def get_fingerprints(cls):
        if cls._fingerprints is None:
            with cls._lock:
                if cls._fingerprints is None:
                    print(" [ModelService] Computing molecular fingerprints...")
                    cls._fingerprints = load_drugbank_with_fingerprints()
        return cls._fingerprints

    @classmethod
    def get_ocr_reader(cls):
        if cls._ocr_reader is None:
            with cls._lock:
                if cls._ocr_reader is None:
                    print(" [ModelService] Loading EasyOCR model (first call only)...")
                    import easyocr
                    cls._ocr_reader = easyocr.Reader(['en'], gpu=False)
        return cls._ocr_reader

    @classmethod
    def warmup(cls):
        """
        Optional: call this once when the app starts (e.g. at the top
        of a Streamlit script, or before opening a Tkinter window) so
        the first real user click isn't the one that pays the load cost.
        """
        cls.get_drug_index()
        cls.get_interactions()
        cls.get_fingerprints()
        cls.get_ocr_reader()
        print(" [ModelService] All models warmed up and cached.\n")


# ────────────────────────────────────────────────────────────
#  OCR HELPERS — always use the shared reader, never load their own
# ────────────────────────────────────────────────────────────
def _run_ocr(image_path, label=""):
    reader = ModelService.get_ocr_reader()
    results = reader.readtext(image_path)
    words = [text for (_, text, conf) in results if conf > OCR_CONFIDENCE]
    combined = ' '.join(words)
    print(f"   OCR [{label}] → {combined}")
    return combined


def _get_text_from_image(image_path, drug_num=1):
    image_path = convert_to_jpg(image_path)
    original_text = _run_ocr(image_path, "original")

    enhanced_path, thresh_path = preprocess(image_path, drug_num)
    enhanced_text = _run_ocr(enhanced_path, "enhanced") if enhanced_path else ""
    thresh_text = _run_ocr(thresh_path, "threshold") if thresh_path else ""

    all_results = [original_text, enhanced_text, thresh_text]
    return max(all_results, key=lambda t: len(t.split()))


# ────────────────────────────────────────────────────────────
#  PUBLIC FUNCTIONS — this is what the frontend actually calls
# ────────────────────────────────────────────────────────────
def identify_from_image(image_path, drug_num=1):
    """
    Identify a drug from a photo (medicine box, blister pack, label).

    Args:
      image_path: path to an image file on disk. If the frontend has
                   the image as bytes/upload object instead of a path
                   (e.g. Streamlit's st.file_uploader), save it to a
                   temp file first and pass that path in here.
      drug_num:    1 or 2, only used to label saved preprocessing output.

    Returns: dict, always has a "found" key.
      {"found": False, "reason": "..."}                         — no text / bad image
      {"found": True, "ocr_text": "...", "matches": [ {...}, ...] }
    """
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        return {"found": False, "reason": f"Unsupported format '{ext}'. Allowed: {SUPPORTED_FORMATS}"}

    size_mb = os.path.getsize(image_path) / (1024 * 1024)
    if size_mb > MAX_IMAGE_MB:
        return {"found": False, "reason": f"Image too large ({size_mb:.1f} MB). Max is {MAX_IMAGE_MB} MB."}

    if not validate_image(image_path):
        return {"found": False, "reason": "Image failed validation."}

    text = _get_text_from_image(image_path, drug_num=drug_num)
    if not text.strip():
        return {"found": False, "reason": "No text detected in image."}

    index = ModelService.get_drug_index()
    matches = match_drug(text, index)

    return {"found": bool(matches), "ocr_text": text, "matches": matches}


def identify_from_name(name):
    """
    Identify a drug by typed name (manual entry, no image).

    Returns: {"found": bool, "matches": [ {...}, ... ]}
    """
    name = (name or "").strip()
    if not name:
        return {"found": False, "reason": "No name provided.", "matches": []}

    index = ModelService.get_drug_index()
    matches = match_drug(name, index)
    return {"found": bool(matches), "matches": matches}


def identify_from_smiles(smiles, min_similarity=0.7):
    """
    Fallback: identify a drug by molecular structure (Tanimoto
    similarity) when a SMILES string is known but the name couldn't
    be matched by text.

    Returns: {"found": bool, "matches": [ {...}, ... ]}
    """
    smiles = (smiles or "").strip()
    if not smiles:
        return {"found": False, "reason": "No SMILES provided.", "matches": []}

    fingerprints = ModelService.get_fingerprints()
    matches = find_similar_drugs(smiles, fingerprints, top_n=5, min_similarity=min_similarity)
    return {"found": bool(matches), "matches": matches}


def check_drug_interaction(drug1_id, drug2_id):
    """
    Check if two identified drugs (by DrugBank ID) have a known
    interaction.

    Returns: {"found": bool, "description": "..."}
    """
    interactions_df = ModelService.get_interactions()
    return check_interaction(drug1_id, drug2_id, interactions_df)


# ────────────────────────────────────────────────────────────
#  Quick manual test — run this file directly to sanity check
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ModelService.warmup()

    print("\n--- Testing identify_from_name ---")
    print(identify_from_name("paracetamol"))

    print("\n--- Testing identify_from_smiles ---")
    print(identify_from_smiles("CC(=O)Nc1ccc(O)cc1"))

    print("\n--- Testing check_drug_interaction ---")
    print(check_drug_interaction("DB00945", "DB01050"))