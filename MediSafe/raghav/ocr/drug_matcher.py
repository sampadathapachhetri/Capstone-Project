# ═══════════════════════════════════════════════════════════════
# drug_matcher.py
# 3-stage drug matching:
#   Stage 1: Exact match    (fastest)
#   Stage 2: Fuzzy match    (handles typos)
#   Stage 3: Tanimoto       (molecular similarity fallback)
#            Uses local SMILES data — no API needed
# ═══════════════════════════════════════════════════════════════

import pandas as pd
import re
from .config import DRUGBANK_CSV, FUZZY_THRESHOLD, MIN_TOKEN_LENGTH
from rapidfuzz import fuzz, process
import pandas as pd
from typing import Optional, Tuple

# ── Lazy import for Tanimoto ──────────────────────────────────
# Only loaded if Stage 1 and 2 both fail
# Saves memory when not needed
_tanimoto_fingerprints = None

def _get_tanimoto_fingerprints():
    """
    Load Tanimoto fingerprints lazily.
    Only computed once, cached after first use.
    Avoids slow startup when exact/fuzzy matching works.
    """
    global _tanimoto_fingerprints
    if _tanimoto_fingerprints is None:
        from .tanimoto_match import load_drugbank_with_fingerprints
        print("🧬 Loading Tanimoto fingerprints (first time only)...")
        _tanimoto_fingerprints = load_drugbank_with_fingerprints()
        print(f"✅ Tanimoto ready: "
              f"{len(_tanimoto_fingerprints):,} fingerprints")
    return _tanimoto_fingerprints


# Main fuzzy matching code starts here


from pathlib import Path
import os
class DrugMatcher:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        if not DrugMatcher._initialized:
            self._load_data()
            DrugMatcher._initialized = True
    
    def _load_data(self):
        """Load data from CSV file - called only once"""
        filepath = os.path.join(Path(__file__).resolve().parent, r"data/cleaned_synonym_id_cn_data.csv")
        
        try:
            df = pd.read_csv(filepath, usecols=['synonym', 'drugbank_id'])
            df = df.dropna(subset=['synonym', 'drugbank_id'])
            self.data = df[['synonym', 'drugbank_id']].values.tolist()
            self.synonyms = [row[0] for row in self.data]
            self.ids = [row[1] for row in self.data]
            print(f"Loaded {len(self.data)} records (singleton instance)")
        except FileNotFoundError:
            print(f"Error: CSV file not found at {filepath}")
            # Initialize with empty data to avoid further errors
            self.data = []
            self.synonyms = []
            self.ids = []
            raise
    
    def match(self, query: str, high_confidence_threshold: float = 0.7) -> Tuple[Optional[str], Optional[str]]:
        if not query or not query.strip():
            return None, "Empty search query"
        
        # Check if data is loaded
        if not self.synonyms:
            return None, "No data available for matching"
        
        results = process.extract(
            query, 
            self.synonyms,
            scorer=fuzz.ratio,
            limit=1,
            score_cutoff=high_confidence_threshold * 100
        )
        
        if not results:
            return None, f"No matches found for '{query}'"
        
        match, score, idx = results[0]
        return self.ids[idx], None

# Main fuzzy matcher ends here 

# How to use 
# from ocr.drug_matcher  import DrugMatcher
#     matcher = DrugMatcher()
#     drug_id, error = matcher.match("Goserelin")



def build_index(df):
    """
    Build searchable index of drug names + synonyms.
    Also stores SMILES per drug for Tanimoto fallback.
    """
    index = {}

    def add(term, entry):
        key = term.strip().lower()
        if key:
            index.setdefault(key, []).append(entry)

    for _, row in df.iterrows():
        db_id  = row.get('drugbank_id', '').strip()
        cname  = row.get('common_name', '').strip()
        syns   = row.get('synonyms',    '').strip()
        smiles = row.get('smiles',      '').strip()

        if not db_id:
            continue

        base = {
            'drugbank_id': db_id,
            'common_name': cname,
            'smiles'     : smiles  # stored for Tanimoto use
        }

        if cname:
            add(cname, {**base, 'matched_synonym': cname})
        if syns:
            for syn in re.split(r'[|;,]', syns):
                syn = syn.strip()
                if syn:
                    add(syn, {**base, 'matched_synonym': syn})

    print(f"✅ Index built: {len(index):,} searchable terms")
    return index


def extract_tokens(text):
    """Extract word/phrase candidates from text"""
    cleaned = re.sub(
        r'[^a-zA-Z0-9\s\-]', ' ', text
    ).lower().strip()
    tokens  = set()
    words   = cleaned.split()

    for w in words:
        if len(w) >= MIN_TOKEN_LENGTH:
            tokens.add(w)
    for n in (2, 3):
        for i in range(len(words) - n + 1):
            tokens.add(' '.join(words[i:i+n]))

    return sorted(tokens, key=len, reverse=True)


def fuzzy_score(a, b):
    """Approximate string similarity using RapidFuzz."""
    if not a or not b:
        return 0.0
    return fuzz.token_sort_ratio(a, b) / 100.0


def _get_smiles_for_token(token, index):
    """
    Helper: find SMILES for the best fuzzy match of a token.
    Used to bridge text → SMILES for Tanimoto.

    Searches index for closest name match,
    returns its SMILES if found.

    Args:
      token: search word/phrase
      index: drug search index

    Returns:
      smiles string or None
    """
    best_score  = 0
    best_smiles = None

    for key, entries in index.items():
        score = fuzzy_score(token, key)
        if score > best_score:
            for entry in entries:
                if entry.get('smiles'):
                    best_score  = score
                    best_smiles = entry['smiles']

    # Only use if reasonably similar (above 0.5)
    # Lower threshold than fuzzy matching since
    # we're just getting a SMILES starting point
    if best_score >= 0.5:
        return best_smiles
    return None


def match_drug(text, index, fuzzy_threshold=FUZZY_THRESHOLD):
    """
    3-stage drug matching pipeline.

    Stage 1: Exact match
      → checks if any token exactly matches a drug name
      → fastest, most reliable
      → returns immediately if found

    Stage 2: Fuzzy match
      → Jaccard character similarity
      → handles OCR typos e.g. "Paracetmol" → "Paracetamol"
      → returns if score above threshold (0.75)

    Stage 3: Tanimoto (NEW — uses your local SMILES data)
      → only runs if Stage 1 and 2 both fail
      → finds best fuzzy match → gets its SMILES
      → compares SMILES against all 14,616 drugs
      → returns most structurally similar drug
      → no internet/API needed — uses your CSV

    Args:
      text:            OCR text or typed drug name
      index:           drug search index from build_index()
      fuzzy_threshold: minimum score for fuzzy match

    Returns:
      list of match dicts sorted by score
    """
    candidates = extract_tokens(text)
    seen_ids   = set()
    matches    = []

    # ── Stage 1: Exact Match ──────────────────────────────────
    print("\n🔍 Stage 1: Exact matching...")
    for token in candidates:
        if token in index:
            for entry in index[token]:
                uid = entry['drugbank_id']
                if uid not in seen_ids:
                    seen_ids.add(uid)
                    matches.append({
                        **entry,
                        'match_type': 'exact',
                        'score'     : 1.0,
                        'ocr_token' : token
                    })
                    print(f"  ✅ EXACT '{token}'"
                          f" → {uid} ({entry['common_name']})")

    if matches:
        return matches

    # ── Stage 2: Fuzzy Match ──────────────────────────────────
    print("  No exact match")
    print("\n🔍 Stage 2: Fuzzy matching...")

    for token in candidates:
        for key, entries in index.items():
            score = fuzzy_score(token, key)
            if score >= fuzzy_threshold:
                for entry in entries:
                    uid = entry['drugbank_id']
                    if uid not in seen_ids:
                        seen_ids.add(uid)
                        matches.append({
                            **entry,
                            'match_type': 'fuzzy',
                            'score'     : round(score, 3),
                            'ocr_token' : token
                        })

    matches.sort(key=lambda x: x['score'], reverse=True)

    if matches:
        for m in matches[:3]:
            print(f"  🔶 FUZZY '{m['ocr_token']}'"
                  f" ≈ '{m['matched_synonym']}'"
                  f" → {m['drugbank_id']}"
                  f" (score={m['score']})")
        return matches

    # ── Stage 3: Tanimoto (local SMILES — no API) ─────────────
    print("  No fuzzy match")
    print("\n🔍 Stage 3: Tanimoto molecular similarity...")
    print("   (using local DrugBank SMILES data)")

    # Find SMILES for best partial match from index
    query_smiles = None
    for token in candidates[:5]:  # try top 5 tokens only
        query_smiles = _get_smiles_for_token(token, index)
        if query_smiles:
            print(f"  🧬 Query SMILES found via '{token}'")
            print(f"     {query_smiles[:60]}...")
            break

    if not query_smiles:
        print("  ❌ Could not find SMILES for query")
        print("  ❌ No match found in any stage")
        return []

    # Load fingerprints (cached after first use)
    fingerprints = _get_tanimoto_fingerprints()

    # Find structurally similar drugs
    from .tanimoto_match import find_similar_drugs
    tanimoto_results = find_similar_drugs(
        query_smiles,
        fingerprints,
        top_n=5,
        min_similarity=0.6  # slightly lower threshold
                             # since we're using an approximate
                             # SMILES as starting point
    )

    for result in tanimoto_results:
        uid = result['drugbank_id']
        if uid not in seen_ids:
            seen_ids.add(uid)
            matches.append({
                'drugbank_id'    : uid,
                'common_name'    : result['common_name'],
                'smiles'         : result['smiles'],
                'matched_synonym': result['common_name'],
                'match_type'     : 'tanimoto',
                'score'          : result['score'],
                'ocr_token'      : 'molecular similarity'
            })

    if matches:
        matches.sort(key=lambda x: x['score'], reverse=True)
        print(f"  ✅ Tanimoto found {len(matches)} similar drug(s)")
        for m in matches[:3]:
            print(f"  🔬 '{m['common_name']}'"
                  f" → {m['drugbank_id']}"
                  f" (similarity={m['score']})")
        return matches

    print("  ❌ No match found in any stage")
    return []