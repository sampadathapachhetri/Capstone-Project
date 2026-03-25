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

## 📖 Description

The system is designed to:

- Provide users with drug interaction information
- Offer a user-friendly interface for input and results

## ⚙️ Installation Guide (Development Setup)

Follow these steps to set up the project locally for development:

### 1. Install Python

Make sure you have **Python 3.14** installed on your system.

Download from:
https://www.python.org/downloads/

---

### 2. Clone the Repository

```bash
git clone -b dev "https://github.com/Roshanchg/capstone.git"
cd capstone
```

---

### 3. Create Virtual Environment (Recommended)

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

Install required modules from the provided `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

### 5. Environment Configuration

Create a `.env` file in the root directory using `.env.example` as a template.

```bash
cp .env.example .env
```

Fill in the required values such as:

- `SECRET_KEY`
- Database credentials
- Debug settings

#### Generate Django Secret Key

You can generate a secure secret key using:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

### 6. Database Setup (Development)

This development setup uses **SQL-based database (default Django setup)**.

Run the following commands:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 7. Create Admin User

```bash
python manage.py createsuperuser
```

Follow the prompts to create your admin credentials.

---

## ▶️ Execution Guide

Run the development server:

```bash
python manage.py runserver
```

Then open your browser and go to:

```
http://127.0.0.1:8000/
```

---

## 🚀 Production Setup (Recommended)

For deploying in production:

### 1. Install Apache with mod_wsgi

Guide:
https://docs.djangoproject.com/en/stable/howto/deployment/wsgi/modwsgi/

---

### 2. Install PostgreSQL

Download and setup PostgreSQL:
https://www.postgresql.org/download/

---

### 3. Configure Production Environment

- Update `.env` with production values
- Use PostgreSQL as database
- Configure Apache + mod_wsgi with Django project

---

## 📝 Notes

- This project is intended for educational purposes.
- Not intended for real medical decision-making.
- Contributions and improvements are welcome.

---
