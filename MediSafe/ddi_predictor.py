"""
DDI Severity Prediction - Minimal Predictor
Loads model and predicts.
"""

import os
import joblib
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
from pathlib import Path

from Levenshtein import distance as levenshtein_distance


class DDIPredictor:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DDIPredictor, cls).__new__(cls)
            cls._instance.loaded = False
        return cls._instance
    
    def load_models(self, model_dir="drug_models"):
        try:
            model_dir = os.path.join(Path(__file__).resolve().parent, "drug_models")
            self.model = joblib.load(os.path.join(model_dir, 'best_model.pkl'))
            
            self.le_drug = joblib.load(os.path.join(model_dir, 'le_combined.pkl'))
            self.le_target = joblib.load(os.path.join(model_dir, 'le_target.pkl'))
            self.metadata = joblib.load(os.path.join(model_dir, 'metadata.pkl'))
            self.known_drugs = set(self.metadata.get('known_drug_ids', []))
            self.loaded = True
            
            model_name = self.metadata.get('best_model_name', 'Unknown')
            print(f"✅ Models loaded ({model_name})")
            return True
        except Exception as e:
            print(f"❌ Failed to load: {e}")
            self.loaded = False
            return False
    
    def predict(self, drug1, drug2):
        if not self.loaded:
            return {'error': 'Models not loaded'}
        
        d1, d2 = drug1.strip().upper(), drug2.strip().upper()
        
        unknown = [x for x in [d1, d2] if x not in self.known_drugs]
        if unknown:
            return {'error': f'Unknown drug ID(s): {unknown}'}
        
        d1_enc = self.le_drug.transform([d1])[0]
        d2_enc = self.le_drug.transform([d2])[0]
        
        lev_sim = 1.0 - (levenshtein_distance(d1, d2) / max(len(d1), len(d2), 1))
        
        def num(x):
            try:
                return float(x.replace('DB', ''))
            except:
                return 0.0
        
        n1, n2 = num(d1), num(d2)
        
        X = pd.DataFrame([[
            d1_enc, d2_enc, lev_sim,
            abs(n1 - n2), n1 + n2,
            min(n1, n2) / max(n1, n2, 1),
            0, 0, 0, 0
        ]], columns=[
            'drug1_encoded', 'drug2_encoded', 'lev_similarity',
            'drug_id_diff', 'drug_id_sum', 'drug_id_ratio',
            'desc_word_count', 'desc_has_cyp', 'desc_has_excret', 'desc_has_serum'
        ])
        
        pred = self.model.predict(X)[0]
        probs = self.model.predict_proba(X)[0]
        severity = self.le_target.inverse_transform([pred])[0]
        
        return {
            'drug1': d1,
            'drug2': d2,
            'severity': severity,
            'confidence': float(max(probs)),
            'probabilities': dict(zip(self.le_target.classes_, probs.tolist()))
        }


predictor = DDIPredictor()

def predict(drug1, drug2):
    """Simple function to predict DDI severity."""
    return predictor.predict(drug1, drug2)

def get_severity(drug1, drug2):
    """Return just the severity string."""
    result = predictor.predict(drug1, drug2)
    return result.get('severity') if 'error' not in result else None
def get_severity_level(drug1, drug2):
    severity = get_severity(drug1, drug2)
    
    if severity is None:
        return None
    
    severity_map = {
        'Low': 1,
        'Moderate-Metabolism': 2,
        'Moderate-Other': 2,
        'High': 3
    }
    
    return severity_map.get(severity)

# ============================================================
# TEST
# ============================================================

# if __name__ == "__main__":
#     predictor.load_models()
    
#     # Test
#     result = predict("DB00001", "DB06605")
    
#     if 'error' not in result:
#         print(f"\n{result['drug1']} + {result['drug2']}")
#         print(f"Severity: {result['severity']}")
#         print(f"Confidence: {result['confidence']*100:.2f}%")
#     print(get_severity("DB00001","DB06605"))
#     print(get_severity_level("DB00001","DB06605"))
    