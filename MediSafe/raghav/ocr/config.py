# config.py
# Central configuration file — all paths and settings in one place
# Update paths here if you move files


import os
from pathlib import Path
#  Base project directory 
BASE_DIR = Path(__file__).resolve().parent #raghav 

#  Dataset paths 
DRUGBANK_CSV     = os.path.join(BASE_DIR, "data", "drugbank_vocabulary_with_smiles.csv")
INTERACTIONS_CSV = os.path.join(BASE_DIR, "data", "interactions_with_severity.csv")

#  Output directory for preprocessed images 
RESULTS_DIR = os.path.join(BASE_DIR, "results", "ocr_results")

#  Image settings 
MAX_IMAGE_MB      = 10    # maximum allowed image size in MB
MIN_IMAGE_SIZE    = 1000  # minimum width/height in pixels before resizing up
MAX_IMAGE_SIZE    = 4000  # maximum width/height before resizing down
OCR_CONFIDENCE    = 0.3   # minimum EasyOCR confidence score to accept text
FUZZY_THRESHOLD   = 0.75  # minimum similarity score for fuzzy drug matching
MIN_TOKEN_LENGTH  = 3     # minimum character length for a word to be considered

#  Supported image formats 
SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff']

#  Create output directory if it doesn't exist 
os.makedirs(RESULTS_DIR, exist_ok=True)