import easyocr
import cv2

print("🔍 Initializing EasyOCR...")
reader = easyocr.Reader(['en'], gpu=False)

# Change this to your image filename
image_path = "medicine.jpg"

print("📸 Reading image...")
results = reader.readtext(r"C:\Users\ragha\Documents\College\8th sem\Capstone project-I\drug_project\medicine2.webp")

print("\n📋 Extracted Text:")
print("-" * 40)
for (bbox, text, confidence) in results:
    print(f"Text: {text:25} | Confidence: {confidence:.2f}")

print("-" * 40)
all_text = ' '.join([text for (_, text, conf) in results if conf > 0.3])
print(f"\n✅ Combined text:\n{all_text}")