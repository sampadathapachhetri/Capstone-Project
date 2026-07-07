from django.apps import AppConfig


class MedisafeConfig(AppConfig):
    name = 'MediSafe'
    def ready(self):
        try:
            print("Pre Loading OCR")
            from raghav.ocr import OCRService
            ocr_service=OCRService()
            print("Loaded successfully")
        except Exception as e: 
            print(f"OCR service preloading failed: {e}")
