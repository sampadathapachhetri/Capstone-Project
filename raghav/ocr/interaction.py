# Checks if two identified drugs have a known interaction
# in the DrugBank interactions database.
#
# Uses interactions_with_severity.csv which contains:
#   drug1_id, drug2_id, description, severity

import pandas as pd
from .config import INTERACTIONS_CSV


def load_interactions(csv_path=INTERACTIONS_CSV):
    """
    Load drug interaction dataset into a DataFrame.

    The interactions file has rows like:
      drug1_id | drug2_id | description | severity

    Args:
      csv_path: path to interactions CSV file

    Returns:
      df: interactions DataFrame
    """
    df = pd.read_csv(csv_path, dtype=str).fillna('')
    print(f" Interactions loaded: {len(df):,} known pairs")
    return df


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