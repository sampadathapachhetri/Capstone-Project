# run_waitress.py
import os
import sys

sys.path.append(r"C:\Users\VICTUS\Documents\capstone\capstone")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "capstone.settings")

from waitress import serve
from capstone.wsgi import application

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Waitress on port 8888")
    print("Access your site through Apache at http://localhost")
    print("=" * 60)
    
    serve(
        application,
        host='127.0.0.1',
        port=8888,
        threads=4,
        # Remove any static file serving - Apache handles it!
    )