# drug_matcher.py
# Matches extracted OCR text to drug names in DrugBank database.
#
# Matching strategy (in order):
#   1. Exact match  — finds perfect word matches (fastest)
#   2. Fuzzy match  — finds similar words (handles OCR typos)
#
# Uses drugbank_vocabulary_with_smiles.csv which contains:
#   - Drug ID, Name, Synonyms, SMILES


import pandas as pd
import re
from config import DRUGBANK_CSV, FUZZY_THRESHOLD, MIN_TOKEN_LENGTH


def load_drugbank(csv_path=DRUGBANK_CSV):
    """
    Load DrugBank vocabulary CSV into a DataFrame.
    Normalizes column names to standard keys regardless
    of how DrugBank names them in different versions.

    Returns:
      df: cleaned DataFrame with columns:
          drugbank_id, common_name, synonyms, smiles
    """
    # Load CSV, treat all columns as strings, fill empty cells with ''
    df = pd.read_csv(csv_path, dtype=str).fillna('')

    # Normalize column names:
    # lowercase, strip spaces, replace spaces with underscores
    # e.g. "DrugBank ID" → "drugbank_id"
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

    # Map actual column names to standard keys
    # Handles different DrugBank CSV versions
    col_map = {}
    for col in df.columns:
        if 'drugbank' in col and 'id' in col:
            col_map['drugbank_id'] = col
        elif col in ('common_name', 'name', 'drug_name', 'generic_name'):
            col_map['common_name'] = col
        elif 'synonym' in col:
            col_map['synonyms'] = col
        elif 'smiles' in col:
            col_map['smiles'] = col

    if 'drugbank_id' not in col_map:
        raise ValueError(" Could not find DrugBank ID column in CSV!")

    df = df.rename(columns=col_map)
    print(f" DrugBank loaded: {len(df):,} drugs")
    return df


def build_index(df):
    """
    Build a searchable dictionary from the drug database.
    Maps every drug name and synonym to its DrugBank entry.

    Structure:
      index = {
        'aspirin'      : [{'drugbank_id': 'DB00945', ...}],
        'acetylsalicylic acid': [{'drugbank_id': 'DB00945', ...}],
        'paracetamol'  : [{'drugbank_id': 'DB00316', ...}],
        ...
      }

    All keys are lowercase for case-insensitive matching.
    Both common names and synonyms are indexed.

    Args:
      df: DrugBank DataFrame from load_drugbank()

    Returns:
      index: dictionary mapping term → list of drug entries
    """
    index = {}

    def add(term, entry):
        """Add a term → entry mapping to the index"""
        key = term.strip().lower()
        if key:
            # Multiple drugs can share a name (different salts etc.)
            index.setdefault(key, []).append(entry)

    for _, row in df.iterrows():
        db_id  = row.get('drugbank_id', '').strip()
        cname  = row.get('common_name', '').strip()
        syns   = row.get('synonyms',    '').strip()
        smiles = row.get('smiles',      '').strip()

        # Skip rows with no drug ID
        if not db_id:
            continue

        # Base entry stored for every term of this drug
        base = {
            'drugbank_id': db_id,
            'common_name': cname,
            'smiles'     : smiles
        }

        # Index the common name (e.g. "Aspirin")
        if cname:
            add(cname, {**base, 'matched_synonym': cname})

        # Index all synonyms (e.g. "Acetylsalicylic acid", "ASA")
        # Synonyms are separated by |, ;, or ,
        if syns:
            for syn in re.split(r'[|;,]', syns):
                syn = syn.strip()
                if syn:
                    add(syn, {**base, 'matched_synonym': syn})

    print(f" Search index built: {len(index):,} searchable terms")
    return index


def extract_tokens(text):
    """
    Extract meaningful word/phrase candidates from OCR text.
    Used to generate search queries against the drug index.

    Process:
      1. Clean text (remove special characters)
      2. Extract single words (≥3 chars)
      3. Extract 2-word phrases (bigrams)
      4. Extract 3-word phrases (trigrams)
      5. Sort by length (try longest matches first)

    Why bigrams/trigrams?
      Some drug names are multi-word:
      e.g. "Vitamin C", "Calcium Carbonate"

    Args:
      text: raw OCR text string

    Returns:
      tokens: sorted list of candidate search terms
    """
    # Remove special characters except letters, numbers, spaces, hyphens
    cleaned = re.sub(r'[^a-zA-Z0-9\s\-]', ' ', text).lower().strip()
    tokens  = set()
    words   = cleaned.split()

    # Single words
    for w in words:
        if len(w) >= MIN_TOKEN_LENGTH:
            tokens.add(w)

    # Bigrams (2-word phrases)
    # Trigrams (3-word phrases)
    for n in (2, 3):
        for i in range(len(words) - n + 1):
            tokens.add(' '.join(words[i:i+n]))

    # Sort longest first — multi-word matches are more specific
    return sorted(tokens, key=len, reverse=True)


def jaccard_score(a, b):
    """
    Calculate similarity between two strings using Jaccard index.
    Measures character-level overlap between two words.

    Formula: |A ∩ B| / |A ∪ B|
      where A and B are sets of characters

    Examples:
      jaccard('aspirin', 'aspirin') = 1.0  (identical)
      jaccard('asprin',  'aspirin') = 0.83 (one missing char)
      jaccard('aspirin', 'ibuprofen') = 0.3 (very different)

    Args:
      a, b: strings to compare

    Returns:
      score: float between 0.0 (no overlap) and 1.0 (identical)
    """
    a_set = set(a.lower())
    b_set = set(b.lower())
    if not a_set or not b_set:
        return 0.0
    return len(a_set & b_set) / len(a_set | b_set)


def match_drug(text, index, fuzzy_threshold=FUZZY_THRESHOLD):
    """
    Match input text to drug database.

    Two-stage matching:
      Stage 1 — EXACT:
        Check if any token exactly matches a drug name/synonym
        Fast O(1) dictionary lookup
        Returns immediately if match found

      Stage 2 — FUZZY (fallback):
        If no exact match, compare each token to every index key
        using Jaccard character similarity
        Catches OCR errors: "Paracetmol" → "Paracetamol"
        Slower but more robust

    Args:
      text:            OCR text or manually typed drug name
      index:           drug search index from build_index()
      fuzzy_threshold: minimum similarity score (default 0.75)

    Returns:
      matches: list of matching drug entries sorted by score
               each entry has: drugbank_id, common_name,
               smiles, matched_synonym, match_type, score
    """
    candidates = extract_tokens(text)
    seen_ids   = set()   # track already found drug IDs (avoid duplicates)
    matches    = []

    #  Stage 1: Exact Match 
    print("\nStage 1: Exact matching...")
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
                    print(f"   EXACT  '{token}'"
                          f" → {uid} ({entry['common_name']})")

    # If exact match found — return immediately (no need for fuzzy)
    if matches:
        return matches

    #  Stage 2: Fuzzy Match 
    print("  No exact match found")
    print("\n Stage 2: Fuzzy matching...")

    for token in candidates:
        for key, entries in index.items():
            score = jaccard_score(token, key)

            # Only accept matches above similarity threshold
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

    # Sort by similarity score (best match first)
    matches.sort(key=lambda x: x['score'], reverse=True)

    # Show top fuzzy matches found
    for m in matches[:3]:
        print(f"   FUZZY  '{m['ocr_token']}'"
              f" ≈ '{m['matched_synonym']}'"
              f" → {m['drugbank_id']}"
              f" (score={m['score']})")

    return matches