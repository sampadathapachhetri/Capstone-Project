import pytesseract
from PIL import Image

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Verify Tesseract is working
try:
    version = pytesseract.get_tesseract_version()
    print(f"✅ Tesseract working! Version: {version}")
except Exception as e:
    print(f"❌ Error: {e}")