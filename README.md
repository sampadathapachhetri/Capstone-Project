# 💊 Web-Based Drug Interaction Checker

## 📌 Introduction

This project is a **web-based drug interaction checker** developed using Django. It allows users to analyze potential interactions between different medications through a simple and accessible web interface.

This is a **capstone project** developed collaboratively by a group of students.

**Group Members:**

- Sampada Thapa Chettri
- Roshan Chaulagain
- Pratik Acharya
- Raghav Raj Shrestha
- Urvi Timilsina

> ⚠️ Note: The Dockerization is not Completely Finished. This is just a source code minor information. Documentation will be updated soon with manual.

---

## 📖 Description

The system is designed to:

- Provide users with drug interaction information
- Offer a user-friendly interface for input and results

---

# ⚙️ Installation Guide (Manual Setup)

### 1. Install Python

Make sure you have **Python 3.14** installed on your system.

Download from:
[https://www.python.org/downloads/](https://www.python.org/downloads/)

---

### 2. Clone the Repository

```bash
git clone "https://github.com/sampadathapachhetri/Capstone-Project"
cd capstone
```

---

### 3. Create Virtual Environment (Optional, breaks sometime for whatever reasons IDK its annoying)

```bash
python -m venv venv
```

Activate it:

- Windows:

```bash
venv\Scripts\activate
```

- macOS/Linux:

```bash
source venv/bin/activate
```

---

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 5. Install and Configure PostgreSQL

This project requires **PostgreSQL** to be installed locally.

Download and install it from:
[https://www.postgresql.org/download/](https://www.postgresql.org/download/)

After installing:

1. Create a **database** and a **user** for the project (you can use `psql`, `pgAdmin`, or any Postgres client).

```sql
CREATE DATABASE your_db_name;
CREATE USER your_db_user WITH PASSWORD 'your_db_password';
GRANT ALL PRIVILEGES ON DATABASE your_db_name TO your_db_user;
```

2. ⚠️ **Important:** The `DB_NAME`, `DB_USER`, and `DB_PASSWORD` (and any other DB-related fields) you set in your `.env` file **must exactly match** the database name and username/password you created above. Mismatched credentials will cause connection errors during migration.

---

### 6. Environment Configuration

Create a `.env` file in the root directory using `.env.example` as a template.

```bash
cp .env.example .env
```

⚠️ **Important:**

- Paste your generated **Django SECRET_KEY** into the `.env` file exactly as shown in `.env.example`
- Fill in all required values (database name, database user, database password, debug, etc.) — these must match the PostgreSQL database/user you created in Step 5

#### Generate Django Secret Key

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

### 7. Download Required Data Files

Some CSV data files used by the app are not included in the repository and must be downloaded manually and placed in specific folders.

#### a) Root-level data files

Download the following files from Google Drive (link to be updated):

- `cleaned_drugbank_id_cn_smiles_syno_data.csv` — **https://drive.google.com/file/d/1pJwmww097vjZ6XiIJ2_V25T_yhRWSGJv/view?usp=sharing**
- `interactions_with_id.csv` — **https://drive.google.com/file/d/1cssECyAEMBEV55wm0Gy90tC5gApTv6Hx/view?usp=sharing**

Place both files directly in the **project root**, at:

```
capstone/cleaned_drugbank_id_cn_smiles_syno_data.csv
capstone/interactions_with_id.csv
```

#### b) OCR module data files

Download the following files from Google Drive (link to be updated):

- `cleaned_drugbank_id_cn_smiles_syno_data.csv` — **https://drive.google.com/file/d/1pJwmww097vjZ6XiIJ2_V25T_yhRWSGJv/view?usp=sharing**
- `cleaned_synonym_id_cn_data.csv` — **https://drive.google.com/file/d/1x9gepqpJDo1mnA8XetHge_-3wIPs8iT2/view?usp=sharing**

First, create the destination folder if it doesn't already exist:

```bash
mkdir -p MediSafe/raghav/ocr/data
```

Then place both files (keeping the **exact same filenames**) at:

```
capstone/MediSafe/raghav/ocr/data/cleaned_drugbank_id_cn_smiles_syno_data.csv
capstone/MediSafe/raghav/ocr/data/cleaned_synonym_id_cn_data.csv
```

> ⚠️ Note: `cleaned_drugbank_id_cn_smiles_syno_data.csv` is required in **both** locations (project root and the OCR data folder) — download/copy it to each path shown above.

---

### 8. Database Migration

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 9. Create Admin User

```bash
python manage.py createsuperuser
```

---

## ▶️ Run Development Server

```bash
python manage.py runserver
```

Open in browser:

```
http://127.0.0.1:8000/
```

---

# 🐳 Docker Setup Guide

This project also supports running using **Docker**.

## 📦 Prerequisites

Make sure you have installed:

- Docker
- Docker Compose
- Docker Desktop (If in windows)

---

## 🧱 Project Structure (Important)

Inside the project (`capstone`) folder:

```
capstone/
│
├── docker-compose.yaml
├── docker/
│   └── apache/
│       ├── apache2.conf
│       └── django.conf
```

---

## ⚙️ Environment Setup for Docker

Create `.env` file:

```bash
cp .env.example .env
```

⚠️ Make sure:

- You paste the Django `SECRET_KEY` correctly (same format as `.env.example`)
- Database and debug values are properly set

---

## ▶️ Run with Docker

Build and start the containers:

```bash
docker-compose up --build
```

Run in background (optional):

```bash
docker-compose up -d
```

---

## 🌐 Access the Application

After containers start, open:

```
http://localhost/
```

(or the configured port if different)

---

## 🛑 Stop Containers

```bash
docker-compose down
```

---

## 📝 Notes

- This project is for educational purposes only
- Not intended for real medical decisions
- Contributions are welcome
- The manual setup is shown to run in development server, hence make sure to make DEBUG=True in your env file
