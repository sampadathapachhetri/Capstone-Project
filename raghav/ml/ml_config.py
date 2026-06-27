# ml_config.py
# Central configuration for the ML model comparison pipeline.
# Keeps sample sizes, paths, and hyperparameters in one place.

import os

#  Base paths 
BASE_DIR     = r"C:\Users\ragha\Documents\College\9th sem\CapStone-2\drug_project"
DATA_DIR     = os.path.join(BASE_DIR, "data")
RESULTS_DIR  = os.path.join(BASE_DIR, "results", "ml_results")

DRUGBANK_CSV     = os.path.join(DATA_DIR, "drugbank_vocabulary_with_smiles.csv")
INTERACTIONS_CSV = os.path.join(DATA_DIR, "interactions_with_severity.csv")
TARGETS_CSV      = os.path.join(DATA_DIR, "drug target identifiers.csv")
ENZYMES_CSV      = os.path.join(DATA_DIR, "drug enzyme identifiers.csv")

os.makedirs(RESULTS_DIR, exist_ok=True)

#  Sampling settings 
N_POSITIVE_SAMPLES = 50_000   # known interacting pairs to sample
N_NEGATIVE_SAMPLES  = 50_000   # non-interacting pairs to generate

#  Train/test split settings 
TEST_SIZE    = 0.2     # 20% held out for testing
RANDOM_STATE = 42       # for reproducibility — same split every run

#  Output file for the built feature dataset 
FEATURES_OUTPUT = os.path.join(RESULTS_DIR, "ml_features.csv")