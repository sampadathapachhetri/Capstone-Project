from ocr import ocr_engine
from ocr.ocr_engine import OCRService
import time
def checkGPU():
    import torch
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU count: {torch.cuda.device_count()}")
        print(f"GPU name: {torch.cuda.get_device_name(0)}")
    else:
        print("CUDA NOT available - check installation")
if __name__ =="__main__":
    # ocr_service=OCRService()
    # start= time.perf_counter()
    # ocr_service.run_ocr(r"C:\Users\VICTUS\Documents\capstone\Capstone-Project\raghav\tests\images\download (1).jpg")
    # end= time.perf_counter()
    # print(f"Time: {end-start}")
    # checkGPU()
    from ocr.drug_matcher  import DrugMatcher
    matcher = DrugMatcher()
    drug_id, error = matcher.match("Goserelin")
    print(drug_id)

