from django.contrib.auth.hashers import make_password,check_password
import uuid
import re
from django.core.mail import send_mail
from .raghav.ocr.ocr_engine import OCRService
from .raghav.ocr.drug_matcher import DrugMatcher
from . import models
from django.conf import settings
import smtplib
from email.mime.text import MIMEText
import random,string
def hash_password(plaintext):
    return make_password(plaintext)

def auth_password(plaintext,pass_hash):
    return check_password(plaintext,pass_hash)

def sanitize_filename(filename,max_length=20):
    if "." in filename:
        name_parts=filename.rsplit(".",1)
        name=name_parts[0]
        ext=name_parts[1]
    else:
        name=filename
        ext=''
    name=re.sub(r'[^a-zA-Z0-9]','_',name)
    if len(name)>max_length:
        name=name[:max_length]
    return f"{name}.{ext}"
def get_profile_upload_path(instance,filename):
    uniqueId=uuid.uuid4().hex[:12]
    uploadPath=f'profile_pics/{uniqueId}/{sanitize_filename(filename=filename)}'
    return uploadPath

def isValidEmail(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+$'
    return bool(re.match(pattern, email))


def createActivityLog():
    pass

def sendEmail(to:str, message:str,subject="Default Subject"):
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=30)
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = settings.EMAIL_HOST_USER
        msg['To'] = to
        server.send_message(msg)
        server.quit()
        return None
    except Exception as e:
        print(f"Error: {e}")
        return "Failed to send email"

def getUserFromSession(session):
    userId=session['user_id']
    try:
        user=models.Users.objects.get(id=userId)
        return user
    except:
        return None

def runFzMatchingForAllWords(value:str):
    words =value.split("=")
    foundvalue=None
    dm=DrugMatcher()
    for word in words: 
        if(len(word)<3 and (";" in word)):
            continue
        # print(f"\nsearching for word: {word}")
        (_,error)=dm.match(word)
        # print(f"\nResponse={temp},{error}")
        if(error==None):
            foundvalue=word
            break
    return foundvalue


def generateRandomOTP():
     return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    