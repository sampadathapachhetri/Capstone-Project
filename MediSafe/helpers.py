from django.contrib.auth.hashers import make_password,check_password
import uuid
import re
def hash_password(plaintext):
    return make_password(plaintext)

def auth_password(plaintext,pass_hash):
    return check_password(plaintext=plaintext,pass_hash=pass_hash)


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


