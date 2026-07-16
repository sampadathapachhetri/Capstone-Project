import psycopg
from dotenv import load_dotenv
from pathlib import Path
import os

baseDir = Path(__file__).resolve().parent
load_dotenv(baseDir / '.env')

host = os.environ.get("DB_HOST")
name = os.environ.get("DB_NAME")
user = os.environ.get("DB_USER")
password = os.environ.get("DB_PASSWORD")

drug_filename = "cleaned_drugbank_id_cn_smiles_syno_data.csv"
interaction_filename = "interactions_with_id.csv"

def load_drugs():
    try:
        with psycopg.connect(
            host=host,
            dbname=name,
            user=user,
            password=password
        ) as conn:
            with conn.cursor() as cur:
                with open(drug_filename, 'r', encoding='utf-8') as f:
                    with cur.copy('COPY "MediSafe_drug"(drug_bank_id,common_name,synonyms,smile_structure) FROM STDIN WITH CSV HEADER') as copy:
                        while data := f.read(8192):
                            copy.write(data)
            conn.commit()
        print(f"✅ Drugs loaded from {drug_filename}")
    except FileNotFoundError:
        print(f"❌ File not found: {drug_filename}")
    except psycopg.Error as e:
        print(f"❌ Database error (drugs): {e}")
import csv

import csv
import psycopg

def load_interactions():
    try:
        with psycopg.connect(
            host=host,
            dbname=name,
            user=user,
            password=password
        ) as conn:
            with conn.cursor() as cur:
                # Get existing drug IDs
                cur.execute('SELECT drug_bank_id FROM "MediSafe_drug"')
                existing_drugs = {row[0] for row in cur.fetchall()}
                print(f"✅ Found {len(existing_drugs)} drugs in database")
                
                with open(interaction_filename, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader)
                    
                    batch = []
                    inserted = 0
                    skipped = 0
                    batch_size = 100000
                    
                    for row in reader:
                        drug1 = row[1]
                        drug2 = row[2]
                        
                        if drug1 not in existing_drugs or drug2 not in existing_drugs:
                            skipped += 1
                            continue
                        
                        batch.append((int(row[0]), drug1, drug2, row[3], row[4], int(row[5])))
                        
                        if len(batch) >= batch_size:
                            cur.executemany(
                                """INSERT INTO "MediSafe_drug_interactions" 
                                   (id, first_drug_id, second_drug_id, description, severity, severity_level) 
                                   VALUES (%s, %s, %s, %s, %s, %s)""",
                                batch
                            )
                            inserted += len(batch)
                            print(f"   Inserted {inserted} rows, skipped {skipped}")
                            batch = []
                            conn.commit()
                    
                    # Insert remaining
                    if batch:
                        cur.executemany(
                            """INSERT INTO "MediSafe_drug_interactions" 
                               (id, first_drug_id, second_drug_id, description, severity, severity_level) 
                               VALUES (%s, %s, %s, %s, %s, %s)""",
                            batch
                        )
                        inserted += len(batch)
                        conn.commit()
                    
        print(f"✅ Inserted {inserted} rows, skipped {skipped} rows (drugs not in database)")
    except FileNotFoundError:
        print(f"❌ File not found: {interaction_filename}")
    except psycopg.Error as e:
        print(f"❌ Database error (interactions): {e}")
if __name__ == "__main__":
    load_drugs()
    load_interactions()