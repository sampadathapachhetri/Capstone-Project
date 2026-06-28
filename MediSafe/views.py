from django.shortcuts import render,redirect
from django.http import Http404,HttpRequest,HttpResponse,JsonResponse
from . import helpers,models
from django.urls import reverse
from django.conf import settings as ds
import requests

def logout(request):
    try:
        request.session.flush()
    except:
        pass
    return redirect('login')

def index(request):
    context={}
    error={}
    message={}
    profile={}
    page={'current':"dashboard"}
    try:
        request.session['user_id']
        userId=request.session['user_id']
        try:
            error=request.session.get("error")
            context['error']=error
            del request.session['error']
        except:
            pass
        try:
            user=models.Users.objects.get(id=userId)
            username=user.full_name
            profile["username"]=username
            if " " in username:
                shortName=username.split(" ")[0]+" " +username.split(" ")[1][0]+"."
            else:
                shortName=username
            profile['username_short']=shortName
            
            context["profile"]=profile
            context['page']=page
            return render(request=request,template_name="MediSafe/index.html", context=context)
        except:
            return redirect("login")
    except:
        return redirect("login")


def createAuthSession(request,userID,exp=0):
    request.session['user_id']=f'{userID}'
    request.session.set_expiry(exp)
    
def login(request):
    context={}
    error={
        # "invalid_cred":"invalid email or password",
        # "empty_field":"The fields must not be empty",
        # "unknown":"Unknown Error occured",
    }
    info={}
    if(request.method=="POST"):    
        email=request.POST.get("email")
        if( not helpers.isValidEmail(email=email)):
            error["invalid_cred"]="Invalid email or password"
        password=request.POST.get("password")
        isRemember=request.POST.get("remember")
        userId=authenticate(email=email,password=password)
        if(userId):
            createAuthSession(request=request,userID=userId)
            return redirect('index')
        else:
            error["invalid_cred"]='Invalid email or password'
    if(error):
        context["error"]=error
    try:
        info["session_exists"]=request.session['user_id']
        username=models.Users.objects.get(id=info['session_exists']).full_name
        info['username']=username
        context["info"]=info
    except:
        pass
    return render(request=request,template_name="MediSafe/login.html",context=context)

def register(request):
    context={}

    error={
        # "invalid_cred":"invalid email or password",
        # "empty_field":"The fields must not be empty",
        # "unknown":"Unknown Error occured",
    }
    message={
        # "redirect":"registered account"
    }
    if request.method=="POST":
        fullName=request.POST.get("fullname")
        email=request.POST.get("email")
        password=request.POST.get("password")
        confirmPassword=request.POST.get("confirm_password")

        if(password!=confirmPassword):
            error['invalid_cred']="Password does not match"
        elif(len(password)<8):
            error['invalid_cred']="Password must be atleast 8 characters long"
        elif(not helpers.isValidEmail(email=email)):
            error['invalid_cred']="Invallid email"
        elif(len(fullName)<4):
            error['invalid_cred']="Full name must be more than 4 characters"
        elif (email_exists(email=email)):
            error['invalid_cred']='Email Already exists'
        else:
            newUser=models.Users.objects.create_user_and_profile(
                full_name=fullName,
                email=email,
                password=password)
            createAuthSession(request=request,userID=newUser.id,exp=0)
            return redirect('index')
        
        if error:
            context["error"]=error
        
        return render(request=request,template_name='MediSafe/register.html',context=context)

    return render(request=request,template_name='MediSafe/register.html',context=context)

def resetPassword(request):
    return render(request=request,template_name='MediSafe/resetAccount.html',context={})

def dashboard(request):
    return render(request=request,template_name='MediSafe/dashboard.html',context={})

def drugCheck(request):
    return render(request=request,template_name='MediSafe/drugCheck.html',context={})

def history(request):
    return render(request=request,template_name='MediSafe/history.html',context={})

def medications(request):
    user=models.Users.objects.get(id=request.session.get("user_id"))
    userMedications=models.UserMedications.objects.filter(user=user)
    context={}
    medications=userMedications
    context['medications']=medications
    return render(request=request,template_name='MediSafe/medications.html',context=context)

def deleteMedication(request,medicationId):
    if(medicationId):
        try:
            user=models.Users.objects.get(id=request.session.get('user_id'))
            medication=models.UserMedications.objects.filter(id=medicationId,user=user)
            medication.delete()
            return redirect(reverse('index')+"?page=medications")
        except:
            pass
    return redirect('index')

def settings(request):
    context={}
    error={}
    try:
        userId=request.session['user_id']
    except:
        return redirect("login")
    if(request.method == "POST"):
        fullname=request.POST.get("fullname")
        email=request.POST.get("email")
        if(fullname!=""):
            if len(fullname)<4:
                error['msg']="Too Short name"
        if(email!=""):
            if(not helpers.isValidEmail(email)):
                error.setdefault('msg',"")
                if error["msg"]:
                    error["msg"]+=" , " 
                error['msg']+="Invalid email"
            else:
                if(email_exists(email)):
                    error.setdefault('msg',"")
                    if error['msg']:
                        error["msg"]+=" , "
                    error['msg']+="Email already exists"
        if error:
            request.session['error']={'settings':error}
            return redirect(reverse('index')+"?page=settings")

        tfa=request.POST.get("tfa")=="on"
        safetyAlerts=request.POST.get("safety_alerts")=="on"
        monthlyUsageReports=request.POST.get("monthly_usage_reports")=="on"
        userId=request.session.get("user_id")
        user=models.Users.objects.update_user_settings(
            user_id=userId, email=email,full_name=fullname,safety_alerts=safetyAlerts,two_factor_auth=tfa,monthly_usage_reports=monthlyUsageReports
        )
        return redirect(reverse('index')+"?page=settings")
    else:
        try:
            user=models.Users.objects.select_related('profile').get(id=userId)
            context['user']=user
            return render(request=request,template_name='MediSafe/settings.html',context=context)

        except:
            return redirect("login")

    

def addMedications(request):
    error={}
    if request.method=="POST":
        try:
            medication_name=request.POST.get("medication_name")
            dosage_unit=request.POST.get("dosage_unit")
            dosage_value=request.POST.get("dosage_value")
            dosage_frequency=request.POST.get("dosage_frequency")
            medication_more=request.POST.get("medication_more")
            try:
                float(dosage_value)
            except :
                error['msg']="INVALID medication input (dosage value)"
                request.session['error']={'addmedications':error}
                return redirect(reverse('index')+"?page=medications")
            if dosage_unit=='g':
                dosage_value=float(dosage_value)*1000
            user=models.Users.objects.get(id=request.session.get("user_id"))

            medicationRow=models.UserMedications.objects.get_or_create(
                user=user,
                name=medication_name,
                dosage_amount_mg=dosage_value,
                dosage_frequency=dosage_frequency,
                medication_more=medication_more
            )
        except:
            pass

        return redirect(reverse('index')+"?page=medications")
        
    else:
        return render(request=request,template_name='MediSafe/addMedications.html',context={})

def intAnalysis(request):
    return render(request=request,template_name='MediSafe/intAnalysis.html',context={})



def authenticate(email,password):
    if(email_exists(email=email)):
        user =models.Users.objects.get(email=email)
        if (helpers.auth_password(plaintext=password,pass_hash=user.pass_hash)):
            return f'{user.id}'
    return None
def email_exists(email):
    try:
        models.Users.objects.get(email=email)
        return True
    except:
        return False


def github_login(request):
    authorize_url="https://github.com/login/oauth/authorize"
    redirect_url=ds.GITHUB_REDIRECT_URI
    
    params={
        'client_id':ds.GITHUB_CLIENT_ID,
        'redirect_uri':redirect_url,
        'scope':"user:email",
    }
    
    auth_url=f"{authorize_url}?client_id={params['client_id']}&redirect_uri={params['redirect_uri']}&scope={params['scope']}"
    return redirect(auth_url)
    
def github_callback(request):
    code=request.GET.get('code')
    token_resp=requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept":"application/json"},
        data={
            "client_id":ds.GITHUB_CLIENT_ID,
            "client_secret":ds.GITHUB_CLIENT_SECRET,
            "code":code,
        }
    )
    access_token=token_resp.json()["access_token"]
    user_resp=requests.get(
        "https://api.github.com/user",
        headers={"Authorization":f"Bearer {access_token}"}
    )
    print(f"RESPONSE: {user_resp}")
    github_user=user_resp.json()
    if(github_user['name']):
        full_name=github_user['name']
    else:
        full_name=github_user['login']   
    provider="github"
    provider_name="GitHub"
    provider_user_id=github_user['id']
    
    newUser=models.Users.objects.create_oauth_user_and_profile(
     full_name=full_name,
     provider=provider,
     provider_name=provider_name,
     provider_user_id=provider_user_id,
     access_token=access_token,
    )
    if(newUser==None):
        return redirect(login)
    createAuthSession(request=request,userID=newUser.id)
    return redirect(index)