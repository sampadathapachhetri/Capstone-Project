from django.shortcuts import render,redirect,get_object_or_404
from django.http import Http404,HttpRequest,HttpResponse,JsonResponse
from . import helpers,models
from django.urls import reverse
from django.conf import settings as ds
import requests
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import uuid
from .raghav.ocr.ocr_engine import OCRService
from django.conf import settings
from .raghav.ocr.drug_matcher import DrugMatcher
import json
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Count,Q
from datetime import timedelta
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
    user = helpers.getUserFromSession(request.session)
    if user is None:
        return redirect('login')
    
    pretty_username = user.full_name.split(" ")[0]
    
    # Get all user history
    history = models.UserHistory.objects.filter(user=user)
    
    # Basic counts
    total_checks = history.count()
    
    # Monthly checks
    now = timezone.now()
    first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    currentmonth_checks = history.filter(date_time__gte=first_day_of_month).count()
    
    # Last month checks
    last_month = first_day_of_month - timedelta(days=1)
    first_day_of_last_month = last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    lastmonth_checks = history.filter(
        date_time__gte=first_day_of_last_month,
        date_time__lt=first_day_of_month
    ).count()
    
    # Percentage change
    if lastmonth_checks > 0:
        percentage_value = int(((currentmonth_checks - lastmonth_checks) / lastmonth_checks) * 100)
        percentage_change = "increase" if percentage_value >= 0 else "decrease"
    else:
        percentage_value = 100 if currentmonth_checks > 0 else 0
        percentage_change = "increase" if currentmonth_checks > 0 else "no_change"
    
    # High risk alerts (severity level 7-10)
    total_highrisk_alerts = history.filter(interaction__severity_level__gte=3).count()
    
    # Recent 5 checks
    recent_checks = history.select_related(
        'interaction__first_drug',
        'interaction__second_drug'
    ).only(
        'id', 'date_time',
        'interaction__severity',
        'interaction__severity_level',
        'interaction__first_drug__common_name',
        'interaction__second_drug__common_name'
    ).order_by('-date_time')[:5]
    
    context = {
        "pretty_username": pretty_username,
        "currentmonth_checks": currentmonth_checks,
        "lastmonth_checks": lastmonth_checks,
        "percentage_change": percentage_change,
        "percentage_value": percentage_value,
        "total_checks": total_checks,
        "total_highrisk_alerts": total_highrisk_alerts,
        "recent_checks": recent_checks,
    }
    
    return render(request, 'MediSafe/dashboard.html', context)

def drugCheck(request):
    return render(request=request,template_name='MediSafe/drugCheck.html',context={})


def validateDrug(request):
    if request.method=="GET":
        drugname=request.GET.get("drugname")
        error=None
        if(drugname==None):
            error="Invalid Drug Name"
        elif drugname.strip()=="":
            error="Invalid Drug Name"
        
        commonName="Unidentified"
        drugbankId="Unidentified"
        drugname=drugname.strip()
        matcher=DrugMatcher()
        (drugbankId,error)=matcher.match(drugname)
        try:
            drug=models.Drug.objects.get(drug_bank_id=drugbankId)
            commonName=drug.common_name
        except Exception as e: 
            if(error==None):
                error="Drugname not found in the Database"
                print(e)
                         
        responseJson={
            "commonname":commonName,
            "synonym":drugname,
            "drugbankId":drugbankId,
            "error":error
        } 
        
        return JsonResponse(responseJson)

def extractName(request):
    ocr_service=OCRService()
    if request.method!="POST":
        return JsonResponse({"error":"Method not allowed"},status=405)
    
    if 'image' not in request.FILES:
        return JsonResponse({"error":"No File provided"},status=400)
    file =request.FILES['image']
    valid_types=['image/jpeg','image/png','images/jpg']
    if file.content_type not in valid_types:
        return JsonResponse({'error':'Only JPG and PNG allowed'},status=400)
    
    file_extension = os.path.splitext(file.name)[1] 
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path =default_storage.save(unique_filename,ContentFile(file.read()))
    absolute_path = os.path.join(settings.MEDIA_ROOT, file_path)
    name=ocr_service.run_ocr(image_path=absolute_path);
    foundval=helpers.runFzMatchingForAllWords(value=name)
    success=True
    if (foundval==None):
        success=False
    else:
        name=foundval
    return JsonResponse({
        'success':success,
        'commonname':name
    })
def history(request):
    page = request.GET.get('page', 1)
    empty=True
    user=helpers.getUserFromSession(request.session)
    if(user==None):
        return redirect("login")
    page_obj = get_user_history_page(user=user, page_number=page)
    context={
        'empty':empty,
        "page_obj":page_obj
    }
    
    return render(request=request,template_name='MediSafe/history.html',context=context)

def get_user_history_page(user, page_number, per_page=10):
    history = models.UserHistory.objects.filter(
        user=user
    ).select_related(
        'interaction__first_drug',
        'interaction__second_drug'
    ).only(
        'id', 
        'date_time',
        'interaction__severity',
        'interaction__severity_level',
        'interaction__description',
        'interaction__first_drug__common_name',
        'interaction__first_drug__drug_bank_id',
        'interaction__second_drug__common_name',
        'interaction__second_drug__drug_bank_id'
    )
    
    paginator = Paginator(history, per_page)
    
    try:
        page_obj = paginator.page(page_number)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    return page_obj


def report_detail(request, history_id):
    """View for displaying a single history report"""
    user = helpers.getUserFromSession(request.session)
    if user is None:
        return redirect("login")
    
    history_item = get_object_or_404(
        models.UserHistory, 
        id=history_id, 
        user=user
    )
    
    context = {
        'item': history_item,
    }
    
    return JsonResponse(context)

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
            user=helpers.getUserFromSession(request.session)
            medication=models.UserMedications.objects.filter(id=medicationId,user=user)
            medication.delete()
            return redirect(reverse('index')+"?page=medications")
        except:
            pass
    return redirect('index')

def switchStatusMedication(request,medicationId):
    if(medicationId):
        user=helpers.getUserFromSession(request.session)
        if(not user):
            return redirect('index')
        medication=models.UserMedications.objects.get(id=medicationId,user=user)
        medication.active=not medication.active
        medication.save()
        return redirect(reverse('index')+"?page=medications")
        

def settingsView(request):
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
    error=None
    context={}
    if request.method=="POST":
        print(request.body)
        try:
            data = json.loads(request.body)
            
            medication_name=data.get("medication_name")
            matcher=DrugMatcher()
            (drugbankId,error)=matcher.match(medication_name)
            if(error!=None):
                error="Drug name not found in the Database"
                context={
                    "error":error
                }
                return JsonResponse(context)
            commonname=models.Drug.objects.get(drug_bank_id=drugbankId).common_name
            dosage_unit=data.get("dosage_unit")
            dosage_value=data.get("dosage_value")
            dosage_frequency=data.get("dosage_frequency")
            medication_more=data.get("medication_more")
            try:
                float(dosage_value)
                if(dosage_value.strip()==""):
                    error="Invalid Dosage Value"
                    context={
                        "error":error
                        }
                    return JsonResponse(context)
            except :
                error="Invalid Dosage Value"
                context={
                    "error":error
                }
                return JsonResponse(context)
            if dosage_unit=='g':
                dosage_value=float(dosage_value)*1000
            elif dosage_unit=="mg":
                dosage_value=dosage_value
            else:
                error="Invalid Dosage Unit"
                context={
                    "error":error
                }
                return JsonResponse(context)
            user=models.Users.objects.get(id=request.session.get("user_id"))
            
            
            exists=models.UserMedications.objects.filter(
                    user=user,
                    name=medication_name,
                    dosage_amount_mg=dosage_value,
                    dosage_frequency=dosage_frequency,
                    category=commonname,
                    medication_more=medication_more
                ).exists()
            if(exists):
                error="This Exact Field input was already added."
                context["error"]=error
                return JsonResponse(context)
            else:
                medicationRow=models.UserMedications.objects.get_or_create(
                    user=user,
                    name=medication_name,
                    dosage_amount_mg=dosage_value,
                    dosage_frequency=dosage_frequency,
                    category=commonname,
                    medication_more=medication_more
                )
        except Exception as e:
            error=f"Error: {e}"
            context['error']=error
            return JsonResponse(context)

        return JsonResponse({error:None})
        
    else:
        
        return render(request=request,template_name='MediSafe/addMedications.html',context={})

def intAnalysis(request):
    if request.method=="GET":
        drug1=request.GET.get("drug1")
        drug2=request.GET.get("drug2")        
        
        drug1Name=models.Drug.objects.get(drug_bank_id=drug1).common_name
        drug2Name=models.Drug.objects.get(drug_bank_id=drug2).common_name
        
        description="""Analysis identifies a critical interaction between Aspirin and
          Warfarin, significantly elevating bleeding risks. Supplementary
          moderate interactions involving Lisinopril necessitate increased
          monitoring of renal function and blood pressure stability."""
        severityLevel=2
        severity="High"
        data={
            "drug1":drug1Name,
            "drug2":drug2Name,
            "description":description,
            "severity_level":severityLevel,
            "severity":severity
        }
        error=""
        context={
            "data":data,
            "error":error
        }
        user=helpers.getUserFromSession(session=request.session)
        print(user)
        
        history=models.Drug_Interactions.objects.create_interaction_and_history(
            user=user,drug1=drug1,drug2=drug2,description=description,severity=severity,severityLevel=severityLevel,dateTime=timezone.now()
        )
        
        
        return render(request=request,template_name='MediSafe/intAnalysis.html',context=context)
    else:
        return redirect(index)





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