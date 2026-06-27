import pandas as pd

print("📂 Loading datasets...")

# ── 1. Load all datasets ──────────────────────────────────────────
vocab        = pd.read_csv("drugbank vocabulary.csv")
targets      = pd.read_csv("drug target identifiers.csv")
enzymes      = pd.read_csv("drug enzyme identifiers.csv")
interactions = pd.read_csv("drug_interactions.csv")

print("✅ Files loaded")
print(f"   Vocabulary:    {vocab.shape}")
print(f"   Targets:       {targets.shape}")
print(f"   Enzymes:       {enzymes.shape}")
print(f"   Interactions:  {interactions.shape}")

# ── 2. Clean Vocabulary ───────────────────────────────────────────
print("\n📋 Cleaning vocabulary...")
vocab = vocab[['DrugBank ID', 'Common name', 'Synonyms']].copy()
vocab.columns = ['drug_id', 'name', 'synonyms']
vocab.drop_duplicates(subset='drug_id', inplace=True)
vocab.dropna(subset=['drug_id', 'name'], inplace=True)
print(f"✅ Vocabulary cleaned: {vocab.shape}")

# ── 3. Clean Targets ──────────────────────────────────────────────
print("\n🧬 Cleaning targets...")
targets = targets[['Gene Name', 'Drug IDs']].copy()
targets.columns = ['gene_name', 'drug_ids']
targets.dropna(inplace=True)

targets['drug_id'] = targets['drug_ids'].str.split('; ')
targets = targets.explode('drug_id')
targets['drug_id'] = targets['drug_id'].str.strip()
targets = targets[['drug_id', 'gene_name']].drop_duplicates()
print(f"✅ Targets cleaned: {targets.shape}")

# ── 4. Clean Enzymes ──────────────────────────────────────────────
print("\n⚗️  Cleaning enzymes...")
enzymes = enzymes[['Gene Name', 'Drug IDs']].copy()
enzymes.columns = ['enzyme_name', 'drug_ids']
enzymes.dropna(inplace=True)

enzymes['drug_id'] = enzymes['drug_ids'].str.split('; ')
enzymes = enzymes.explode('drug_id')
enzymes['drug_id'] = enzymes['drug_id'].str.strip()
enzymes = enzymes[['drug_id', 'enzyme_name']].drop_duplicates()
print(f"✅ Enzymes cleaned: {enzymes.shape}")

# ── 5. Clean Interactions ─────────────────────────────────────────
print("\n🔗 Cleaning interactions...")
interactions.columns = ['drug1_id', 'drug2_id', 'description']
interactions.dropna(inplace=True)
interactions.drop_duplicates(inplace=True)
interactions['drug1_id'] = interactions['drug1_id'].str.strip()
interactions['drug2_id'] = interactions['drug2_id'].str.strip()
print(f"✅ Interactions cleaned: {interactions.shape}")

# ── 6. Classify Severity ──────────────────────────────────────────
print("\n🚦 Classifying severity...")

def classify_severity(text):
    if pd.isna(text):
        return 'unknown'

    text = text.lower()

    # ── HIGH ──────────────────────────────────────────────────────
    high_keywords = [
        'contraindicated', 'fatal', 'life-threatening', 'severe',
        'avoid', 'do not use', 'serious', 'dangerous', 'death',
        'toxic', 'overdose', 'hemorrhage', 'cardiac arrest',
        'respiratory depression', 'seizure', 'coma', 'lethal',
        'anaphylaxis', 'anaphylactic', 'serotonin syndrome',
        'neuroleptic malignant', 'torsades de pointes', 'qt prolongation',
        'agranulocytosis', 'aplastic anemia', 'liver failure',
        'renal failure', 'kidney failure', 'hepatotoxic'
    ]

    # ── MODERATE ──────────────────────────────────────────────────
    moderate_keywords = [
        'increase', 'decrease', 'reduce', 'inhibit', 'caution',
        'monitor', 'may affect', 'can affect', 'risk of',
        'elevated', 'altered', 'prolonged', 'excessive',
        'bleeding', 'hypotension', 'hypertension', 'arrhythmia',
        'interaction', 'potentiate', 'enhance', 'antagonize',
        'concentration', 'plasma level', 'bioavailability',
        'metabolism', 'clearance', 'half-life', 'absorption',
        'sedation', 'drowsiness', 'dizziness', 'nausea'
    ]

    # ── LOW ───────────────────────────────────────────────────────
    low_keywords = [
        'minor', 'slight', 'minimal', 'small', 'mild',
        'insignificant', 'unlikely', 'theoretical', 'weak',
        'not expected', 'not likely', 'rarely', 'uncommon',
        'well tolerated', 'no significant', 'not significant',
        'not clinically', 'limited', 'transient', 'temporary',
        'generally safe', 'usually safe', 'no known', 'not known'
    ]

    # Check HIGH first (most critical)
    for word in high_keywords:
        if word in text:
            return 'high'

    # Check LOW before moderate (prevents over-classifying)
    for word in low_keywords:
        if word in text:
            return 'low'

    # Check MODERATE
    for word in moderate_keywords:
        if word in text:
            return 'moderate'

    # Default → low (most unmatched descriptions are minor)
    return 'low'

interactions['severity'] = interactions['description'].apply(classify_severity)

# Numeric label for ML
severity_map = {'low': 0, 'moderate': 1, 'high': 2}
interactions['severity_label'] = interactions['severity'].map(severity_map)

print("✅ Severity classified:")
print(interactions['severity'].value_counts().to_string())

# Severity % breakdown
total = len(interactions)
print("\n📊 Severity Distribution (%):")
for level in ['high', 'moderate', 'low']:
    count = (interactions['severity'] == level).sum()
    pct = (count / total) * 100
    print(f"   {level.capitalize():10} {count:>8,}  ({pct:.1f}%)")

# ── 7. Build Drug Feature Table ───────────────────────────────────
print("\n🏗️  Building drug feature table...")

drug_targets = targets.groupby('drug_id')['gene_name'].apply(
    lambda x: '|'.join(x)
).reset_index()
drug_targets.columns = ['drug_id', 'targets']

drug_enzymes = enzymes.groupby('drug_id')['enzyme_name'].apply(
    lambda x: '|'.join(x)
).reset_index()
drug_enzymes.columns = ['drug_id', 'enzymes']

drug_table = vocab.merge(drug_targets, on='drug_id', how='left')
drug_table = drug_table.merge(drug_enzymes, on='drug_id', how='left')

print(f"✅ Drug feature table built: {drug_table.shape}")

# ── 8. Build Final Interaction Dataset ────────────────────────────
print("\n🔀 Merging all features into final dataset...")

final = interactions.merge(
    drug_table.add_suffix('_drug1').rename(columns={'drug_id_drug1': 'drug1_id'}),
    on='drug1_id', how='left'
)

final = final.merge(
    drug_table.add_suffix('_drug2').rename(columns={'drug_id_drug2': 'drug2_id'}),
    on='drug2_id', how='left'
)

print(f"✅ Final dataset built: {final.shape}")

# ── 9. Make Interactions Symmetric (A→B same as B→A) ─────────────
print("\n🔄 Making interactions symmetric...")

flipped = interactions.rename(columns={
    'drug1_id': 'drug2_id',
    'drug2_id': 'drug1_id'
})[['drug1_id', 'drug2_id', 'description', 'severity', 'severity_label']]

interactions_full = pd.concat([interactions, flipped]).drop_duplicates()
print(f"✅ Symmetric interactions: {interactions_full.shape}")

# ── 10. Save All Files ────────────────────────────────────────────
print("\n💾 Saving files...")

drug_table.to_csv("drug_table.csv", index=False)
interactions_full.to_csv("interactions_with_severity.csv", index=False)
final.to_csv("final_interactions.csv", index=False)

print("\n🎉 All done! Files saved:")
print("   → drug_table.csv                  (drug info + targets + enzymes)")
print("   → interactions_with_severity.csv  (interactions + severity labels)")
print("   → final_interactions.csv          (full ML-ready dataset)")

# ── 11. Final Summary ─────────────────────────────────────────────
print("\n📊 Final Summary:")
print(f"   Total drugs:            {len(drug_table)}")
print(f"   Total interactions:     {len(interactions_full)}")
print(f"   High severity:          {(interactions_full.severity == 'high').sum():,}")
print(f"   Moderate severity:      {(interactions_full.severity == 'moderate').sum():,}")
print(f"   Low severity:           {(interactions_full.severity == 'low').sum():,}")
print(f"   Final ML dataset cols:  {final.shape[1]}")