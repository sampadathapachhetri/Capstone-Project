 # ocr_engine.py
# Handles all OCR (Optical Character Recognition) operations.
# Uses EasyOCR — a deep learning based text extractor that works
# well on real-world medicine packet photos.
#
# Key design decision:
#   EasyOCR reader is loaded ONCE at module import time.
#   This avoids reloading the model for every image (slow).


import easyocr
from .image_utils import convert_to_jpg, preprocess
from .config import OCR_CONFIDENCE

#  Load EasyOCR model once 
# Loading takes ~10 seconds but only happens once
# gpu=False → uses CPU (works on all computers without GPU)
# ['en'] → English language model
print("Loading EasyOCR model (this takes a few seconds)...")
reader = easyocr.Reader(['en'], gpu=True)
print(" EasyOCR ready!\n")


def run_ocr(image_path, label=""):
    """
    Run EasyOCR on a single image and extract text.

    EasyOCR returns for each detected text region:
      - bbox: bounding box coordinates (we don't use this)
      - text: the detected text string
      - conf: confidence score (0.0 to 1.0)

    We filter by confidence to remove unreliable detections.

    Args:
      image_path: path to image file
      label:      label for display (e.g. "Drug 1 Original")

    Returns:
      combined: all detected words joined as one string
    """
    results = reader.readtext(image_path)
    words   = []

    print(f"\n OCR Results — {label}")
    print("-" * 45)

    for (_, text, conf) in results:
        # Only keep text with confidence above threshold
        # Low confidence = OCR is unsure = likely wrong
        if conf > OCR_CONFIDENCE:
            print(f"  {text:30} conf={conf:.2f}")
            words.append(text)

    # Join all detected words into one string for matching
    combined = ' '.join(words)
    print(f"  → Combined: {combined}")

    return combined


def get_text_from_image(image_path, drug_num):
    """
    Full image → text extraction pipeline.

    Runs OCR on THREE versions of the image:
      1. Original  — unmodified image
      2. Enhanced  — contrast/sharpness improved
      3. Threshold — pure black and white

    Different versions work better for different image types:
      - Clear photos    → original often best
      - Dark/dim photos → enhanced often best
      - Simple packets  → threshold often best

    Selects the version with the MOST words detected
    (more words = more text found = better for matching).

    Args:
      image_path: path to original medicine image
      drug_num:   1 or 2 (for labeling outputs)

    Returns:
      best_text: the OCR result with most words found
    """
    print(f"\n Extracting text from Drug {drug_num} image...")

    # Convert to JPG if needed (required for OpenCV)
    image_path = convert_to_jpg(image_path)

    # OCR on original unmodified image
    original_text = run_ocr(image_path, f"Drug {drug_num} — Original")

    # Preprocess then OCR on both versions
    enhanced_path, thresh_path = preprocess(image_path, drug_num)
    enhanced_text = run_ocr(enhanced_path, f"Drug {drug_num} — Enhanced")
    thresh_text   = run_ocr(thresh_path,   f"Drug {drug_num} — Threshold")

    # Pick version with most words detected
    all_results = [original_text, enhanced_text, thresh_text]
    best_text   = max(all_results, key=lambda t: len(t.split()))

    print(f"\n Best result selected: {best_text}")
    return best_text