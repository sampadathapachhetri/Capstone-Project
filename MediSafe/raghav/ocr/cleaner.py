import csv
import re

def split_synonyms_intelligently(synonyms_str):
    """
    Splits synonyms using the 2-character rule:
    - Tokens <= 2 chars are accumulated as prefix patterns (N, 5, Cl, etc.)
    - Tokens >= 3 chars are the start of the actual drug name
    """
    if not synonyms_str:
        return []
    
    synonyms_str = synonyms_str.strip()
    if synonyms_str.startswith('"') and synonyms_str.endswith('"'):
        synonyms_str = synonyms_str[1:-1]
    
    synonyms = []
    current_synonym = []
    bracket_depth = 0
    paren_depth = 0
    in_quotes = False
    buffer = []  # Accumulates prefix tokens like N, 5, Cl
    i = 0
    
    while i < len(synonyms_str):
        char = synonyms_str[i]
        
        # Handle quotes
        if char == '"':
            in_quotes = not in_quotes
            current_synonym.append(char)
            i += 1
            continue
        
        # Track brackets and parentheses
        if not in_quotes:
            if char == '[':
                bracket_depth += 1
            elif char == ']':
                bracket_depth -= 1
            elif char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
        
        # If we're inside brackets or parentheses, treat everything as part of the name
        if bracket_depth > 0 or paren_depth > 0:
            current_synonym.append(char)
            i += 1
            continue
        
        # If we hit a comma and not inside special structures
        if char == ',' and not in_quotes:
            # Finalize the current token
            token = ''.join(current_synonym).strip()
            current_synonym = []
            
            if token:
                # Check if token is a prefix pattern (<= 2 chars) or drug name (>= 3 chars)
                if len(token) <= 2:
                    # Accumulate prefix tokens
                    buffer.append(token)
                else:
                    # This is the start of the drug name
                    # Combine buffer with this token
                    if buffer:
                        full_name = ','.join(buffer) + '-' + token
                        synonyms.append(full_name)
                        buffer = []
                    else:
                        synonyms.append(token)
            
            i += 1
            continue
        
        current_synonym.append(char)
        i += 1
    
    # Handle the last token
    if current_synonym:
        token = ''.join(current_synonym).strip()
        if token:
            if len(token) <= 2:
                buffer.append(token)
            else:
                if buffer:
                    full_name = ','.join(buffer) + '-' + token
                    synonyms.append(full_name)
                    buffer = []
                else:
                    synonyms.append(token)
    
    # If there's anything left in buffer (shouldn't happen, but just in case)
    if buffer:
        synonyms.append(','.join(buffer))
    
    # Clean up any remaining quotes
    synonyms = [s.strip('"\'') for s in synonyms if s.strip()]
    
    return synonyms

def process_drug_list(input_file, output_file):
    rows = []
    
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        header = next(reader)
        
        try:
            drugbank_idx = header.index('DrugBank ID')
            common_name_idx = header.index('Common name')
            synonyms_idx = header.index('Synonyms')
        except ValueError as e:
            print(f"Error: Could not find required column. {e}")
            print(f"Available columns: {header}")
            return
        
        for row in reader:
            if not row or len(row) <= max(drugbank_idx, common_name_idx, synonyms_idx):
                continue
                
            drugbank_id = row[drugbank_idx].strip()
            synonyms_str = row[synonyms_idx].strip() if len(row) > synonyms_idx else ''
            
            synonyms = split_synonyms_intelligently(synonyms_str)
            
            for synonym in synonyms:
                if synonym.strip():
                    rows.append({
                        'synonym': synonym.strip(),
                        'drugbank_id': drugbank_id
                    })
    
    if rows:
        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            fieldnames = ['synonym', 'drugbank_id']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"Successfully created {output_file}")
        print(f"Total rows: {len(rows)}")
        print(f"Unique drugs: {len(set(row['drugbank_id'] for row in rows))}")
    else:
        print("No data was processed. Please check your input file.")

if __name__ == "__main__":
    input_file = r"data/cleaned_drugbank_id_cn_smiles_syno_data.csv"
    output_file = r"data/cleaned_synonym_id_cn_data.csv"
    
    print(f"Processing: {input_file}")
    process_drug_list(input_file, output_file)