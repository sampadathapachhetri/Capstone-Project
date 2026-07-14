from django.contrib.auth.hashers import make_password,check_password
import uuid
import re
from django.core.mail import send_mail
from .raghav.ocr.ocr_engine import OCRService
from .raghav.ocr.drug_matcher import DrugMatcher
from . import models
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
    send_mail
    pass

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