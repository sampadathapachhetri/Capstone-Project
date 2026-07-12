# Handles all image operations:
#   - Validating image files
#   - Converting image formats to JPG
#   - Preprocessing images for better OCR results


import cv2
import numpy as np
from PIL import Image
import os

from .config import (
    SUPPORTED_FORMATS,
    MAX_IMAGE_MB,
    MIN_IMAGE_SIZE,
    MAX_IMAGE_SIZE,
    RESULTS_DIR
)


def validate_image(image_path):
    """
    Validate image before processing.
    Checks:
      1. File exists on disk
      2. Format is supported (jpg, png, webp etc.)
      3. File size is within limit (default 10 MB)

    Returns:
      True  → image is valid, safe to process
      False → image has a problem, stops pipeline
    """
    # Check 1: Does the file exist?
    if not os.path.exists(image_path):
        print(f" File not found: {image_path}")
        return False

    # Check 2: Is the format supported?
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        print(f" Unsupported format: {ext}")
        print(f" Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        return False

    # Check 3: Is the file size acceptable?
    size_mb = os.path.getsize(image_path) / (1024 * 1024)
    print(f" Image size: {size_mb:.2f} MB")

    if size_mb > MAX_IMAGE_MB:
        print(f"  Image too large! ({size_mb:.1f} MB)")
        print(f"  Maximum allowed: {MAX_IMAGE_MB} MB")
        print(f"  Compress or resize the image first")
        return False

    if size_mb > 5:
        # Warn user but still allow processing
        print(f" Large image ({size_mb:.1f} MB) — processing may be slow")

    return True


def convert_to_jpg(image_path):
    """
    Convert any supported image format to JPG.
    JPG is required for OpenCV processing.

    Handles transparency (RGBA) by converting to RGB first.
    Saves converted image with '_converted.jpg' suffix.

    Args:
      image_path: path to original image

    Returns:
      jpg_path: path to converted JPG image
                (returns original path if already JPG)
    """
    ext = os.path.splitext(image_path)[1].lower()

    # Already JPG — no conversion needed
    if ext in ['.jpg', '.jpeg']:
        return image_path

    # Build output path
    jpg_path = os.path.splitext(image_path)[0] + '_converted.jpg'

    # Convert using PIL
    # .convert("RGB") removes transparency (RGBA) which JPEG doesn't support
    img = Image.open(image_path).convert("RGB")
    img.save(jpg_path, "JPEG", quality=95)

    size_mb = os.path.getsize(jpg_path) / (1024 * 1024)
    print(f" Converted {ext} → jpg ({size_mb:.2f} MB)")

    return jpg_path


def preprocess(image_path, drug_num):
    """
    Enhance medicine image for better OCR text detection.
    Applies a series of image processing steps:
      1. Resize  — ensures image is not too small or too large
      2. Denoise — removes grain/noise from photo
      3. Grayscale — removes color (not needed for text reading)
      4. Sharpen — makes text edges crisper
      5. CLAHE   — improves contrast especially in uneven lighting
      6. Threshold — converts to pure black/white for maximum contrast

    Works for all medicine image types:
      - Medicine boxes/cartons
      - Tablet strips/blister packs
      - Bottle labels

    Args:
      image_path: path to JPG image
      drug_num:   1 or 2 (used for naming output files)

    Returns:
      enhanced_path: path to contrast-enhanced version
      thresh_path:   path to black/white threshold version
      Both saved to results/ocr_results/ folder
    """
    print(f"\n Preprocessing Drug {drug_num} image...")

    # Load image using OpenCV
    img = cv2.imread(image_path)
    if img is None:
        print(" Could not load image!")
        return None, None

    # Show original dimensions
    h, w = img.shape[:2]
    print(f"   Original size: {w}x{h} pixels")

    # Step 1: Resize 
    # Too small → scale up so text is readable
    if w < MIN_IMAGE_SIZE or h < MIN_IMAGE_SIZE:
        img = cv2.resize(img, None, fx=2, fy=2,
                         interpolation=cv2.INTER_CUBIC)
        print(" Step 1: Resized up (2x — image was small)")

    # Too large → scale down to speed up processing
    elif w > MAX_IMAGE_SIZE or h > MAX_IMAGE_SIZE:
        img = cv2.resize(img, None, fx=0.5, fy=0.5,
                         interpolation=cv2.INTER_AREA)
        print(" Step 1: Resized down (0.5x — image was very large)")
    else:
        print(" Step 1: Size OK — no resize needed")

    # Step 2: Denoise 
    # Removes camera grain/noise that confuses OCR
    # Uses colored denoising to preserve detail before grayscale
    denoised = cv2.fastNlMeansDenoisingColored(img, h=10)
    print(" Step 2: Denoised")

    # Step 3: Grayscale 
    # Color is not needed for reading text
    # Grayscale reduces complexity and speeds up OCR
    gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)
    print(" Step 3: Converted to grayscale")

    #  Step 4: Sharpen 
    # Kernel matrix that enhances edges (text strokes)
    # Center value (5) boosts pixel, neighbors (-1) create contrast
    kernel    = np.array([[0, -1,  0],
                          [-1,  5, -1],
                          [0, -1,  0]])
    sharpened = cv2.filter2D(gray, -1, kernel)
    print(" Step 4: Sharpened")

    # Step 5: CLAHE (Contrast Enhancement) 
    # Better than simple histogram equalization
    # Works on small local regions (tileGridSize) separately
    # Handles uneven lighting on medicine packets (reflections, shadows)
    clahe    = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(sharpened)
    print(" Step 5: Contrast enhanced (CLAHE)")

    # Step 6: Threshold 
    # Converts image to pure black and white
    # OTSU method automatically finds the best threshold value
    # Great for medicine packets with clear text on white background
    _, thresh = cv2.threshold(
        enhanced, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    print(" Step 6: Threshold applied (Otsu)")

    # Save both versions 
    enhanced_path = os.path.join(RESULTS_DIR, f"drug{drug_num}_enhanced.jpg")
    thresh_path   = os.path.join(RESULTS_DIR, f"drug{drug_num}_thresh.jpg")
    cv2.imwrite(enhanced_path, enhanced)
    cv2.imwrite(thresh_path,   thresh)
    print(f" Saved → {RESULTS_DIR}")

    return enhanced_path, thresh_path