from pathlib import Path
from raghav.ocr.ocr_engine import OCRService
if __name__=="__main__":
    ocr_service=OCRService()
    print(ocr_service.run_ocr(r"C:\Users\VICTUS\Documents\capstone\capstone\MediSafe\raghav\tests\images\download (1).jpg"))