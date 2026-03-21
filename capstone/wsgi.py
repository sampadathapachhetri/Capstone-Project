import os
import sys

# Path to your project
sys.path.append(r"C:\Users\VICTUS\Documents\capstone\capstone")
sys.path.append(r"C:\Users\VICTUS\Documents\capstone\capstone\capstone")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "capstone.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()