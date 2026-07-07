# Matches drugs using molecular structure similarity (SMILES)
# instead of text-based name matching.
#
# Used as a FALLBACK when exact/fuzzy matching fails to find
# a drug — useful for brand names or unusual spellings that
# don't match any text in our database, but might still
# correspond to a known molecule.
#
# Tanimoto coefficient measures similarity between molecular
# fingerprints:
#   similarity = |A ∩ B| / |A ∪ B|
#   Range: 0.0 (no similarity) to 1.0 (identical molecule)


from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator, DataStructs
import pandas as pd

from config import DRUGBANK_CSV


def smiles_to_fingerprint(smiles_string):
    """
    Convert a SMILES string into a Morgan fingerprint (ECFP4).
    Fingerprints encode the chemical structure as a bit vector
    that can be compared for similarity.

    Args:
      smiles_string: SMILES notation (e.g. "CC(=O)Nc1ccc(O)cc1")

    Returns:
      fingerprint: RDKit Morgan fingerprint object
                   or None if SMILES is invalid
    """
    try:
        # Parse SMILES into a molecule object
        mol = Chem.MolFromSmiles(smiles_string)

        if mol is None:
            return None

        # Generate Morgan fingerprint using the modern generator API
        generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
        fingerprint = generator.GetFingerprint(mol)
        return fingerprint

    except Exception:
        return None


def load_drugbank_with_fingerprints(csv_path=DRUGBANK_CSV):
    """
    Load DrugBank vocabulary and pre-compute fingerprints
    for all drugs that have valid SMILES data.

    This is done ONCE at startup since fingerprint generation
    is slow — we don't want to recompute it for every search.

    Args:
      csv_path: path to drugbank_vocabulary_with_smiles.csv

    Returns:
      drug_fingerprints: list of dicts with:
        drugbank_id, common_name, smiles, fingerprint
    """
    print(" Loading DrugBank for Tanimoto matching...")
    df = pd.read_csv(csv_path, dtype=str).fillna('')
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

    # Normalize column names
    col_map = {}
    for col in df.columns:
        if 'drugbank' in col and 'id' in col:
            col_map['drugbank_id'] = col
        elif col in ('common_name', 'name'):
            col_map['common_name'] = col
        elif 'smiles' in col:
            col_map['smiles'] = col

    df = df.rename(columns=col_map)

    # Build list of drugs with valid fingerprints
    drug_fingerprints = []
    skipped = 0

    print(" Computing molecular fingerprints (this may take a minute)...")

    for _, row in df.iterrows():
        smiles = row.get('smiles', '').strip()

        # Skip drugs with no SMILES data
        if not smiles:
            continue

        fingerprint = smiles_to_fingerprint(smiles)

        # Skip invalid SMILES strings
        if fingerprint is None:
            skipped += 1
            continue

        drug_fingerprints.append({
            'drugbank_id' : row.get('drugbank_id', '').strip(),
            'common_name' : row.get('common_name', '').strip(),
            'smiles'      : smiles,
            'fingerprint' : fingerprint
        })

    print(f" Fingerprints ready: {len(drug_fingerprints):,} drugs")
    print(f"   (skipped {skipped} invalid SMILES)")

    return drug_fingerprints


def find_similar_drugs(query_smiles, drug_fingerprints, top_n=5, min_similarity=0.7):
    """
    Find drugs with similar molecular structure to a query SMILES.

    Compares the query molecule's fingerprint against every drug
    in the database using Tanimoto similarity.

    Args:
      query_smiles:       SMILES string to search for
      drug_fingerprints:  pre-computed list from
                           load_drugbank_with_fingerprints()
      top_n:               max number of results to return
      min_similarity:      minimum Tanimoto score to include (0.0-1.0)

    Returns:
      matches: list of dicts sorted by similarity (best first)
               each has: drugbank_id, common_name, smiles, score
    """
    # Convert query SMILES to fingerprint
    query_fp = smiles_to_fingerprint(query_smiles)

    if query_fp is None:
        print(f" Invalid SMILES: {query_smiles}")
        return []

    print(f"\n Comparing against {len(drug_fingerprints):,} drugs...")

    matches = []

    for drug in drug_fingerprints:
        # Calculate Tanimoto similarity between fingerprints
        similarity = DataStructs.TanimotoSimilarity(
            query_fp,
            drug['fingerprint']
        )

        if similarity >= min_similarity:
            matches.append({
                'drugbank_id': drug['drugbank_id'],
                'common_name': drug['common_name'],
                'smiles'     : drug['smiles'],
                'score'      : round(similarity, 3)
            })

    # Sort by similarity score, best first
    matches.sort(key=lambda x: x['score'], reverse=True)

    # Show top results
    print(f" Found {len(matches)} similar drug(s) above threshold {min_similarity}")
    for m in matches[:top_n]:
        print(f"   {m['common_name']:25} ({m['drugbank_id']}) "
              f"→ Tanimoto={m['score']}")

    return matches[:top_n]


def match_by_smiles(query_smiles, drug_fingerprints, min_similarity=0.7):
    """
    Convenience function — find the SINGLE best matching drug
    by molecular structure.

    Args:
      query_smiles:       SMILES to identify
      drug_fingerprints:  pre-computed fingerprint database
      min_similarity:      minimum acceptable score

    Returns:
      drug_id, drug_name, score  OR  None, None, 0 if no match
    """
    matches = find_similar_drugs(
        query_smiles,
        drug_fingerprints,
        top_n=1,
        min_similarity=min_similarity
    )

    if matches:
        best = matches[0]
        return best['drugbank_id'], best['common_name'], best['score']

    return None, None, 0


#  Test standalone 
if __name__ == "__main__":
    # Load fingerprint database
    fingerprints = load_drugbank_with_fingerprints()

    # Test with Paracetamol's SMILES
    test_smiles = "CC(=O)Nc1ccc(O)cc1"  # Paracetamol

    print(f"\n Testing with SMILES: {test_smiles}")
    matches = find_similar_drugs(test_smiles, fingerprints, top_n=5)