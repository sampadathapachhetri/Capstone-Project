import pytesseract
from PIL import Image
import easyocr
import cv2
import time

# ── Setup ─────────────────────────────────────────────────────────
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
image_path = r"C:\Users\ragha\Documents\College\8th sem\Capstone project-I\drug_project\medicine.jpg"

print("=" * 50)
print("       OCR COMPARISON TEST")
print("=" * 50)

# ── Test 1: PyTesseract ───────────────────────────────────────────
print("\n🔵 TEST 1: PyTesseract")
print("-" * 40)

start = time.time()
img = Image.open(image_path)
tesseract_text = pytesseract.image_to_string(img)
tesseract_time = time.time() - start

print(tesseract_text)
print(f"⏱️  Time taken: {tesseract_time:.2f} seconds")

# ── Test 2: EasyOCR ───────────────────────────────────────────────
print("\n🟢 TEST 2: EasyOCR")
print("-" * 40)

start = time.time()
reader = easyocr.Reader(['en'], gpu=False)
results = reader.readtext(image_path)
easyocr_time = time.time() - start

for (bbox, text, confidence) in results:
    print(f"Text: {text:25} | Confidence: {confidence:.2f}")

easyocr_combined = ' '.join([text for (_, text, conf) in results if conf > 0.3])
print(f"\n✅ Combined: {easyocr_combined}")
print(f"⏱️  Time taken: {easyocr_time:.2f} seconds")

# ── Comparison Summary ────────────────────────────────────────────
print("\n" + "=" * 50)
print("         COMPARISON SUMMARY")
print("=" * 50)
print(f"PyTesseract time:  {tesseract_time:.2f} sec")
print(f"EasyOCR time:      {easyocr_time:.2f} sec")
print(f"\nFaster engine: {'PyTesseract ✅' if tesseract_time < easyocr_time else 'EasyOCR ✅'}")
print("=" * 50)