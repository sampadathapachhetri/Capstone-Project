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

> ⚠️ Note: This project is still under development and may not be fully complete.

---

## 📖 Description

The system is designed to:

- Provide users with drug interaction information
- Offer a user-friendly interface for input and results

---

# ⚙️ Installation Guide (Development Setup)

### 1. Install Python

Make sure you have **Python 3.14** installed on your system.

Download from:
[https://www.python.org/downloads/](https://www.python.org/downloads/)

---

### 2. Clone the Repository

```bash
git clone -b dev "https://github.com/Roshanchg/capstone.git"
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

### 5. Environment Configuration

Create a `.env` file in the root directory using `.env.example` as a template.

```bash
cp .env.example .env
```

⚠️ **Important:**

- Paste your generated **Django SECRET_KEY** into the `.env` file exactly as shown in `.env.example`
- Fill in all required values (database, debug, etc.)

#### Generate Django Secret Key

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

### 6. Database Setup (Development)

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 7. Create Admin User

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
│       ├── django.conf
│       └── ssl/
│           ├── cert.pem
│           └── key.pem
```

---

## 🔐 Generate SSL Certificates

The `ssl` directory **must contain** `cert.pem` and `key.pem`.

Run this command from the project root:

```bash
openssl req -x509 -newkey rsa:4096 -keyout docker/apache/ssl/key.pem -out docker/apache/ssl/cert.pem -days 365 -nodes -subj "/CN=localhost"
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

# 🚀 Production Setup (Recommended)

### 1. Install Apache with mod_wsgi

[https://docs.djangoproject.com/en/stable/howto/deployment/wsgi/modwsgi/](https://docs.djangoproject.com/en/stable/howto/deployment/wsgi/modwsgi/)

### 2. Install PostgreSQL

[https://www.postgresql.org/download/](https://www.postgresql.org/download/)

### 3. Configure Production

- Update `.env` with production values
- Use PostgreSQL database
- Configure Apache + mod_wsgi

---

## 📝 Notes

- This project is for educational purposes only
- Not intended for real medical decisions
- Contributions are welcome
