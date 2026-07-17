from django.apps import AppConfig


class MedisafeConfig(AppConfig):
    name = 'MediSafe'
    def ready(self):
        try:
            print("Pre Loading OCR")
            from .raghav.ocr.ocr_engine import OCRService
            ocr_service=OCRService()
            print("Pre loading Array of drug matcher")
            from .raghav.ocr.drug_matcher  import DrugMatcher
            matcher = DrugMatcher()     
                
            print("Loaded successfully")
        except Exception as e: 
            print(f"OCR service preloading failed: {e}")
            
