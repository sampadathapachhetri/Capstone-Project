# ═══════════════════════════════════════════════════════════════
# ocr_engine.py
# Handles all OCR (Optical Character Recognition) operations.
# Uses EasyOCR — a deep learning based text extractor that works
# well on real-world medicine packet photos.
#
# Key design decisions:
#   1. EasyOCR reader is loaded ONCE at module import time.
#      This avoids reloading the model for every image (slow).
#   2. GPU is used automatically if available (NVIDIA + CUDA).
#      Falls back to CPU silently if no GPU found.
# ═══════════════════════════════════════════════════════════════

import torch
import easyocr

from ocr.ocr_engine import run_ocr
from .image_utils import convert_to_jpg, preprocess
from .config      import OCR_CONFIDENCE

# ── Auto-detect GPU ───────────────────────────────────────────
# Checks if NVIDIA GPU + CUDA is available on this machine
# True  → uses RTX 4050 (fast ~0.5-1 sec per image)
# False → uses CPU (slower ~5-8 sec per image)
import torch
import easyocr

# OCR confidence threshold
OCR_CONFIDENCE = 0.50


class OCRService:
    """
    Singleton OCR service.

    The EasyOCR model is loaded only once and reused
    throughout the application's lifetime.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Prevent reinitialization
        if OCRService._initialized:
            return

        # -------------------------------
        # GPU Detection
        # -------------------------------
        self.gpu_available = torch.cuda.is_available()

        if self.gpu_available:
            self.device_name = torch.cuda.get_device_name(0)
            print(f"🚀 GPU detected: {self.device_name}")
            print("🔄 Loading EasyOCR on GPU...")
        else:
            self.device_name = "CPU"
            print("💻 No GPU found — using CPU")
            print("🔄 Loading EasyOCR on CPU (this takes a few seconds)...")

        # -------------------------------
        # Load EasyOCR once
        # -------------------------------
        self.reader = easyocr.Reader(
            ['en'],
            gpu=self.gpu_available
        )

        self.device_label = (
            f"GPU ({self.device_name}) 🚀"
            if self.gpu_available
            else "CPU 💻"
        )

        print(f"✅ EasyOCR ready! Running on: {self.device_label}\n")

        OCRService._initialized = True

    def run_ocr(self, image_path, label=""):
        """
        Run OCR on a single image.

        Args:
            image_path (str): Path to image.
            label (str): Display label.

        Returns:
            str: Combined detected text.
        """

        results = self.reader.readtext(image_path)
        words = []

        print(f"\n📋 OCR Results — {label} [{self.device_label}]")
        print("-" * 45)

        for (_, text, conf) in results:
            if conf > OCR_CONFIDENCE:
                print(f"  {text:30} conf={conf:.2f}")
                words.append(text)

        combined = " ".join(words)

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
    print(f"\n📸 Extracting text from Drug {drug_num} image...")

    # Convert to JPG if needed (required for OpenCV)
    image_path = convert_to_jpg(image_path)

    # OCR on original unmodified image
    original_text = run_ocr(
        image_path,
        f"Drug {drug_num} — Original"
    )

    # Preprocess then OCR on both versions
    enhanced_path, thresh_path = preprocess(image_path, drug_num)
    enhanced_text = run_ocr(
        enhanced_path,
        f"Drug {drug_num} — Enhanced"
    )
    thresh_text = run_ocr(
        thresh_path,
        f"Drug {drug_num} — Threshold"
    )

    # Pick version with most words detected
    # more words = more text found = better for matching
    all_results = [original_text, enhanced_text, thresh_text]
    best_text   = max(all_results, key=lambda t: len(t.split()))

    print(f"\n🏆 Best result selected: {best_text}")
    return best_text