# Checks if two identified drugs have a known interaction
# in the DrugBank interactions database.
#
# Uses interactions_with_severity.csv which contains:
#   drug1_id, drug2_id, description, severity

import pandas as pd
from .config import INTERACTIONS_CSV

_interactions_df = None


def load_interactions(csv_path=INTERACTIONS_CSV):
    """
    Load drug interaction dataset into a DataFrame.

    This function caches the loaded DataFrame so repeated calls
    return the same singleton instance, similar to the OCR model
    loader in `modelservice.py`.

    The interactions file has rows like:
      drug1_id | drug2_id | description | severity

    Args:
      csv_path: path to interactions CSV file

    Returns:
      df: interactions DataFrame
    """
    global _interactions_df
    if _interactions_df is None:
        _interactions_df = pd.read_csv(csv_path, dtype=str).fillna('')
        print(f" Interactions loaded: {len(_interactions_df):,} known pairs")
    return _interactions_df


def fuzzy_match_common_name(text, index, fuzzy_threshold=0.75):
    """
    Fuzzy match only against common drug names.

    This ignores synonyms and only returns results when the
    matched term corresponds to the drug's common name.
    """
    from .drug_matcher import extract_tokens, jaccard_score

    candidates = extract_tokens(text)
    matches = []
    seen_ids = set()

    for token in candidates:
        for key, entries in index.items():
            score = jaccard_score(token, key)
            if score >= fuzzy_threshold:
                for entry in entries:
                    if (entry.get('matched_synonym', '').strip().lower() ==
                            entry.get('common_name', '').strip().lower()):
                        uid = entry['drugbank_id']
                        if uid not in seen_ids:
                            seen_ids.add(uid)
                            matches.append({
                                **entry,
                                'match_type': 'fuzzy_common_name',
                                'score': round(score, 3),
                                'ocr_token': token
                            })

    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches


def check_interaction(drug1_id, drug2_id, interactions_df):
    """
    Check if two drugs have a known interaction.

    Searches BOTH directions:
      drug1 → drug2 AND drug2 → drug1
    Because DrugBank may store the pair in either order.

    Args:
      drug1_id:         DrugBank ID of first drug  (e.g. "DB00945")
      drug2_id:         DrugBank ID of second drug (e.g. "DB01050")
      interactions_df:  loaded interactions DataFrame

    Returns:
      dict with:
        found:       True if interaction exists, False if not
        description: interaction details text
    """
    print(f"\n Checking interaction: {drug1_id} ↔ {drug2_id}")

    # Search both A→B and B→A directions
    result = interactions_df[
        ((interactions_df['drug1_id'] == drug1_id) &
         (interactions_df['drug2_id'] == drug2_id)) |
        ((interactions_df['drug1_id'] == drug2_id) &
         (interactions_df['drug2_id'] == drug1_id))
    ]

    # No interaction found in database
    if result.empty:
        return {
            'found'      : False,
            'description': 'No known interaction found in DrugBank database.'
        }

    # Interaction found — return description
    row = result.iloc[0]
    return {
        'found'      : True,
        'description': row.get(
            'description',
            'Interaction exists but no description available.'
        )
    }