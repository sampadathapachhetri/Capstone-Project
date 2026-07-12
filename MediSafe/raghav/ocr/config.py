# ═══════════════════════════════════════════════════════════════
# config.py
# No hardcoded paths — works on any machine.
# ═══════════════════════════════════════════════════════════════

import os
from dotenv import load_dotenv
from pathlib import Path
# Load .env file (if exists)
# Silent if no .env found — uses defaults instead
load_dotenv()

# ── Base directory (relative to this file) ────────────────────
BASE_DIR = Path(__file__).resolve().parent 

# ── Dataset paths ─────────────────────────────────────────────
DRUGBANK_CSV = os.environ.get(
    'DRUGBANK_CSV',
    os.path.join(BASE_DIR, "data",
                 "drugbank_vocabulary_with_smiles.csv")
)

INTERACTIONS_CSV = os.environ.get(
    'INTERACTIONS_CSV',
    os.path.join(BASE_DIR, "data",
                 "interactions_with_severity.csv")
)

# ── Output directory ──────────────────────────────────────────
RESULTS_DIR = os.environ.get(
    'RESULTS_DIR',
    os.path.join(BASE_DIR, "results", "ocr_results")
)

# ── Image settings ────────────────────────────────────────────
MAX_IMAGE_MB     = int(os.environ.get('MAX_IMAGE_MB',      10))
MIN_IMAGE_SIZE   = int(os.environ.get('MIN_IMAGE_SIZE',  1000))
MAX_IMAGE_SIZE   = int(os.environ.get('MAX_IMAGE_SIZE',  4000))
OCR_CONFIDENCE   = float(os.environ.get('OCR_CONFIDENCE', 0.3))
FUZZY_THRESHOLD  = float(os.environ.get('FUZZY_THRESHOLD',0.75))
MIN_TOKEN_LENGTH = int(os.environ.get('MIN_TOKEN_LENGTH',   3))

# ── Supported formats ─────────────────────────────────────────
SUPPORTED_FORMATS = [
    '.jpg', '.jpeg', '.png',
    '.webp', '.bmp', '.tiff'
]

# ── Create output directory ───────────────────────────────────
os.makedirs(RESULTS_DIR, exist_ok=True)