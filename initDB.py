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

filename = "cleaned_drugbank_id_cn_smiles_syno_data.csv"

try:
    with psycopg.connect(
    host=host,
    dbname=name,
    user=user,
    password=password
    ) as conn:
        with conn.cursor() as cur:
            with open(filename, 'r',encoding='utf-8') as f:
                with cur.copy('COPY "MediSafe_drug"(drug_bank_id,common_name,synonyms,smile_structure) FROM STDIN WITH CSV HEADER') as copy:
                    while data := f.read(8192):
                        copy.write(data)
        conn.commit()
            
except FileNotFoundError:
    print(f"File not found {filename}, make sure to download it from google drive and upload it at <project_dir>/{filename}")
except psycopg.Error as e:
    print(f"Database error: {e}")