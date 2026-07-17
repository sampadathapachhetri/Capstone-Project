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
from .ddi_predictor import get_severity_level


from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import utils
from io import BytesIO
import csv
from datetime import datetime

def logout(request):
    try:
        request.session.flush()
    except:
        pass
    return redirect('login')


def api_canGetAlertNotification(request):
    user=helpers.getUserFromSession(request.session)
    return JsonResponse({"allowed":user.profile.safety_alerts})

def api_canGetReminderNotification(request):
    user=helpers.getUserFromSession(request.session)
    return JsonResponse({"allowed":user.profile.monthly_usage_reports})

def shouldPushReminderNotification(request):
    if(api_canGetReminderNotification(request)):
        user=helpers.getUserFromSession(request.session)
        noti,_=models.NotificationTrigger.objects.get_or_create(user=user)
        response=models.NotificationTrigger.objects.shouldNotificationTrigger(noti)
        if(response):
            models.NotificationTrigger.objects.afterNotificationTriggered(noti)
        
        return JsonResponse({"allowed":response})
    return JsonResponse({"allowed":False})
    
        

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
    
    
def api_is_tfa_enabled(request):
    if request.method == "POST":
        try:
            # Handle both JSON and FormData
            if request.content_type == "application/json":
                data = json.loads(request.body)
                email = data.get("email")
            else:
                email = request.POST.get("email")
            
            if not email:
                return JsonResponse({'enabled': False, 'error': 'Email is required'}, status=400)
            
            user = models.Users.objects.get(email=email)
            return JsonResponse({'enabled': user.profile.two_factor_auth})
            
        except models.Users.DoesNotExist:
            return JsonResponse({'enabled': False, 'error': 'User not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'enabled': False, 'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'enabled': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def is_tfa_enabled(email):
    try:
        user = models.Users.objects.get(email=email)
        return user.profile.two_factor_auth
    except models.Users.DoesNotExist:
        return False


def createAuthSession(request, userID, remember=False):
    request.session['user_id'] = str(userID)
    if remember:
        request.session.set_expiry(1209600) 
    else:
        request.session.set_expiry(0)
    request.session.save()



def login(request):
    context = {}
    error = None
    info = {}
    
    if request.method == "POST":
        response = validate_login(request)
        if response['success']:
            return redirect("index")
        else:
            error = response['msg']
    
    if error:
        context["error"] = {"login_error": error}
    
    try:
        info["session_exists"] = request.session['user_id']
        username = models.Users.objects.get(id=info['session_exists']).full_name
        info['username'] = username
        context["info"] = info
    except:
        pass
    
    return render(request=request, template_name="MediSafe/login.html", context=context)


def validate_login(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "msg": "Method not allowed"})
    
    email = request.POST.get("email")
    password = request.POST.get("password")
    remember = request.POST.get("remember") == "on"
    
    if not email or not password:
        return JsonResponse({"success": False, "msg": "Email and password are required"})
    
    if not helpers.isValidEmail(email=email):
        return JsonResponse({"success": False, "msg": "Invalid email or password"})
    
    userId = authenticate(email=email, password=password)
    print("User",userId)
    if userId is None:
        return JsonResponse({"success": False, "msg": "Invalid User Credentials"})
    
    if is_tfa_enabled(email=email):
        otp = request.POST.get("otp")
        if not otp:
            return JsonResponse({"success": False, "msg": "OTP is required for this account"})
        
        success, error = validateOTP(email=email, otp=otp)
        if not success:
            return JsonResponse({"success": False, "msg": error or "Invalid OTP"})
        else:
            otpObj=models.OTP.objects.get(email=email,otp=otp)
            otpObj.delete()
    createAuthSession(request=request, userID=userId, remember=remember)
    return JsonResponse({"success": True, "msg": None})

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
            createAuthSession(request=request,userID=newUser.id)
            return redirect('index')
        
        if error:
            context["error"]=error
        
        return render(request=request,template_name='MediSafe/register.html',context=context)

    return render(request=request,template_name='MediSafe/register.html',context=context)

def resetPassword(request):
    return render(request=request,template_name='MediSafe/resetAccount.html',context={})

def requestResetPassword(request):
    if request.method=="POST":
        data=json.loads(request.body)
        email=data.get("email")
        otp=data.get("otp")
        newPassword=data.get("password")
        err=None
        if(len(newPassword)<8):
            err="Password must be atleast 8 characters long"
            return JsonResponse({"error":err})
        hashedPass=helpers.hash_password(newPassword)
        (success,err)=validateOTP(email=email,otp=otp)
        if success:
            try:
                user=models.Users.objects.get(email=email)
                if user.is_oauth_user:
                    success=False
                    err="Email is used with OAuth account, login via google or github"
                else:
                    print(f"hashedPass: {hashedPass}")
                    user.pass_hash=hashedPass
                    user.save()
                    otpObj=models.OTP.objects.get(email=email,otp=otp)
                    otpObj.delete()
                    
            except Exception as e:
                success=False
                print("ERROR:" ,e)
                err="Failure, Maybe Retry"
        return JsonResponse({"error":err})
        

def requestOTP(request):
    if request.method=="POST":
        data=json.loads(request.body)
        email=data.get("email")
        otp=helpers.generateRandomOTP()
        msg="Your OTP:\n"+otp
        try:
            user=models.Users.objects.get(email=email)
            if user.is_oauth_user:
                err="Email is used with OAuth account, login via google or github"
                return JsonResponse({"error":err})
            err=helpers.sendEmail(to=email,message=msg,subject="OTP Verification")
            err=None
            if(err==None):
                print(f"Sent to {email}")
                models.OTP.objects.remove_and_create(email=email,otpval=otp)
                return JsonResponse({"error":None})
            else:
                print(f"Failed to send: {email}, Error:{err}")
                return JsonResponse({"error":f"{err}"})
        except Exception as e:
            print("ERROR :",e)
            err="Invalid Email"
            return JsonResponse({"error":err})
        
                    

def validateOTP(email,otp):
    try:
        otpObj=models.OTP.objects.get(email=email)
        print(f"OTP ATTEMPTS:. {otpObj.attempts}")
        otpObj.attempts+=1
        otpObj.save()
        if(otpObj.attempts>settings.MAX_OTP_ATTEMPTS):
            print(f"OTP ATTEMPTS limit excdded, deleting the otp row. {otpObj.attempts}")
            otpObj.delete()
            return (False,"Limit exceeded")
        if(otpObj.otp==otp):
            if(otpObj.expiration_time<timezone.now()):
                return (False,"Expired OTP")
            return (True,None)
        return (False,"Invalid Code")
    except Exception as e:
        print("ERROR in validate OTP: ",e)
        return (False,"Email isnt sent")

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
    total_highrisk_alerts = history.filter(interaction__severity_level__gte=2).count()
    
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
    os.remove(absolute_path)
    return JsonResponse({
        'success':success,
        'commonname':name
    })

def history(request):
    user = helpers.getUserFromSession(request.session)
    if user is None:
        return redirect("login")
    
    page_obj = get_user_history_page(user=user, page_number=1)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request=request, template_name='MediSafe/history.html', context=context)

def api_history_paginated(request):
    try:
        user = helpers.getUserFromSession(request.session)
        if user is None:
            return JsonResponse({
                'success': False,
                'error': 'User not authenticated'
            })
        
        page_number = request.GET.get('page', 1)
        per_page = request.GET.get('per_page', 10)
        
        search_query = request.GET.get('search', '').strip()
        severity_filter = request.GET.get('severity', 'all').strip()
        date_from = request.GET.get('date_from', '').strip()
        date_to = request.GET.get('date_to', '').strip()
        
        history_qs = models.UserHistory.objects.filter(
            user=user
        ).select_related(
            'interaction',
            'interaction__first_drug',
            'interaction__second_drug'
        )
        
        if search_query:
            history_qs = history_qs.filter(
                Q(interaction__first_drug__common_name__icontains=search_query) |
                Q(interaction__second_drug__common_name__icontains=search_query)
            )
        
        # Apply severity filter (if not 'all' or empty)
        if severity_filter and severity_filter != 'all':
            history_qs = history_qs.filter(interaction__severity__iexact=severity_filter)
        
        # Apply date range filters (if provided)
        if date_from:
            history_qs = history_qs.filter(date_time__date__gte=date_from)
        
        if date_to:
            history_qs = history_qs.filter(date_time__date__lte=date_to)
        
        paginator = Paginator(history_qs, per_page)
        
        try:
            page_obj = paginator.page(page_number)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        data = []
        for item in page_obj:
            data.append({
                'id': item.id,
                'date': item.date_time.strftime('%B %d, %Y'),
                'time': item.date_time.strftime('%I:%M %p'),
                'drug1': item.interaction.first_drug.common_name,
                'drug2': item.interaction.second_drug.common_name,
                'severity': item.interaction.severity,
                'severity_level': item.interaction.severity_level,
                'description': item.interaction.description or 'No description available.',
            })
        
        response = {
            'success': True,
            'data': data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'start_index': page_obj.start_index(),
                'end_index': page_obj.end_index(),
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
                'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            }
        }
        
        return JsonResponse(response)
        
    except Exception as e:
        print(f"Error in api_history_paginated: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
    
def getInteractionHistorySingle(request, historyId):
    try:
        user = helpers.getUserFromSession(request.session)
        
        history_entry = models.UserHistory.objects.select_related(
            'interaction',
            'interaction__first_drug',
            'interaction__second_drug'
        ).get(
            user=user,
            id=historyId
        )
        
        inter = history_entry.interaction
        
        response = {
            "success": True,
            "error": None,
            "id":history_entry.id,
            "drug1": inter.first_drug.common_name,
            "drug2": inter.second_drug.common_name,
            "description": inter.description,
            "severity": inter.severity,
            "severity_level": inter.severity_level,
            "checked_date": history_entry.date_time.strftime('%B %d, %Y'),
            "checked_time": history_entry.date_time.strftime('%I:%M %p'),
        }
        
        return JsonResponse(response)
        
    except models.UserHistory.DoesNotExist:
        print(f"UserHistory not found for user {user} with id {historyId}")
        return JsonResponse({
            "success": False,
            "error": "This interaction record no longer exists. It may have been deleted.",
            "should_refresh": True
        })
        
    except Exception as e:
        print(f"Error trying to get interaction card: {e}")
        return JsonResponse({
            "success": False,
            "error": "Unable to load interaction details. Please try again.",
            "should_refresh": False
        })
        
        
def get_user_history_page(user, page_number, per_page=10):
    history = models.UserHistory.objects.filter(
        user=user
    ).select_related(
        'interaction',
        'interaction__first_drug',
        'interaction__second_drug'
    ).only(
        'id', 
        'date_time',
        'interaction__severity',
        'interaction__severity_level',
        'interaction__description',
        'interaction__first_drug__common_name',
        'interaction__second_drug__common_name'
    )
    
    paginator = Paginator(history, per_page)
    
    try:
        page_obj = paginator.page(page_number)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    return page_obj


def report_detail(request, history_id):
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

def api_medications(request):
    try:
        user = models.Users.objects.get(id=request.session.get("user_id"))
        if not user:
            return JsonResponse({
                'success': False,
                'error': 'User not authenticated'
            })
        
        page_number = request.GET.get('page', 1)
        per_page = request.GET.get('per_page', 10)
        
        search_query = request.GET.get('search', '').strip()
        status_filter = request.GET.get('active', 'all').strip()
        
        medications_qs = models.UserMedications.objects.filter(user=user)
        
        if search_query:
            medications_qs = medications_qs.filter(
                Q(name__icontains=search_query) |
                Q(category__icontains=search_query) |
                Q(dosage_frequency__icontains=search_query)
            )
        
        if status_filter and status_filter != 'all':
            if status_filter.lower() == 'true':
                medications_qs = medications_qs.filter(active=True)
            elif status_filter.lower() == 'false':
                medications_qs = medications_qs.filter(active=False)
        
        paginator = Paginator(medications_qs, per_page)
        
        try:
            page_obj = paginator.page(page_number)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        data = []
        for med in page_obj:
            data.append({
                'id': med.id,
                'name': med.name,
                'dosage_amount': float(med.dosage_amount_mg),
                'dosage_frequency': med.dosage_frequency,
                'category': med.category,
                'last_refill': med.last_refill.strftime('%B %d, %Y'),
                'active': med.active,
            })
        
        response = {
            'success': True,
            'data': data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'start_index': page_obj.start_index(),
                'end_index': page_obj.end_index(),
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
                'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            }
        }
        
        return JsonResponse(response)
        
    except Exception as e:
        print(f"Error in api_medications: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


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

    

def deleteAccount(request):
    if request.method=="POST":
        try:
            user=helpers.getUserFromSession(request.session)
            user.delete()
            request.session.flush()
            return JsonResponse({"success":True})
        except Exception as e:
            return JsonResponse({"success":False,"reason":str(e)})
        

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
        firstDrug=models.Drug.objects.get(drug_bank_id=drug1)
        secondDrug=models.Drug.objects.get(drug_bank_id=drug2)
        drug1Name=firstDrug.common_name
        drug2Name=secondDrug.common_name
        description="""The Description for this interaction was not found in the Database. Proceed with caution."""
        interaction=None
        try:
            interaction=models.Drug_Interactions.objects.get(first_drug=firstDrug,second_drug=secondDrug)
        except Exception as e: 
            print(f"Interaction not in DB: {e}")
        if(interaction==None):
            severityLevel = get_severity_level(drug1=drug1,drug2=drug2)
        else:
            severity=interaction.severity_level
            description=interaction.description
            severityLevel=interaction.severity_level
        error=""
        severity="Unidentified"
        match severityLevel:
            case 0:
                severity="Low"   
            case 1: 
                severity="Moderate"   
            case 2:
                severity="High"   
        data={
            "drug1":drug1Name,
            "drug2":drug2Name,
            "description":description,
            "severity_level":severityLevel,
            "severity":severity
        }
        context={
            "data":data,
            "error":error
        }
        user=helpers.getUserFromSession(session=request.session)
        if(interaction==None):
            print("Interaction doesnot exist, creating a new one")
            history=models.Drug_Interactions.objects.create_interaction_and_history(
                user=user,drug1=drug1,drug2=drug2,description=description,severity=severity,severityLevel=severityLevel,dateTime=timezone.now()
            )
        else:
            history=models.Drug_Interactions.objects.create_history_of_interaction(
                user=user,
                interaction=interaction,
                dateTime=timezone.now()
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


def google_login(request):
    authorize_url = "https://accounts.google.com/o/oauth2/v2/auth"
    redirect_url = ds.GOOGLE_REDIRECT_URI
    
    params = {
        'client_id': ds.GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_url,
        'response_type': 'code',
        'scope': 'email profile',
    }
    
    auth_url = f"{authorize_url}?client_id={params['client_id']}&redirect_uri={params['redirect_uri']}&response_type={params['response_type']}&scope={params['scope']}"
    return redirect(auth_url)

def google_callback(request):
    code = request.GET.get('code')
    token_resp = requests.post(
        "https://oauth2.googleapis.com/token",
        headers={"Accept": "application/json"},
        data={
            "client_id": ds.GOOGLE_CLIENT_ID,
            "client_secret": ds.GOOGLE_CLIENT_SECRET,
            "code": code,
            "redirect_uri": ds.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
    )
    access_token = token_resp.json()["access_token"]
    user_resp = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    print(f"RESPONSE: {user_resp}")
    google_user = user_resp.json()
    if google_user.get('name'):
        full_name = google_user['name']
    else:
        full_name = google_user['email']
    provider = "google"
    provider_name = "Google"
    provider_user_id = google_user['id']
    
    newUser = models.Users.objects.create_oauth_user_and_profile(
        full_name=full_name,
        provider=provider,
        provider_name=provider_name,
        provider_user_id=provider_user_id,
        access_token=access_token,
    )
    if newUser == None:
        return redirect(login)
    createAuthSession(request=request, userID=newUser.id)
    return redirect(index)


# ========== COMBINED EXPORT (Medications + History) ==========
def export_combined_pdf(request):
    try:
        user = helpers.getUserFromSession(request.session)
        if user is None:
            return JsonResponse({'error': 'User not authenticated'}, status=401)
        
        # Get data
        medications = models.UserMedications.objects.filter(user=user)
        history = models.UserHistory.objects.filter(
            user=user
        ).select_related(
            'interaction',
            'interaction__first_drug',
            'interaction__second_drug'
        )
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        # Styles
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#005fb8'),
            alignment=TA_CENTER,
            spaceAfter=10
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#64748b'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=8,
            spaceBefore=12
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#334155'),
            spaceAfter=4
        )
        
        # Build content
        story = []
        
        # Header
        story.append(Paragraph("MediSafe Complete Export", title_style))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
        story.append(Paragraph(f"<b>Patient:</b> {user.full_name} | <b>Email:</b> {user.email}", normal_style))
        story.append(Spacer(1, 0.3 * inch))
        
        # ==================== MEDICATIONS SECTION ====================
        story.append(Paragraph("1. Medications", heading_style))
        
        # Medication Summary
        total_meds = medications.count()
        active_meds = medications.filter(active=True).count()
        inactive_meds = total_meds - active_meds
        
        med_summary_data = [
            ['Total Medications', 'Active', 'Inactive'],
            [str(total_meds), str(active_meds), str(inactive_meds)]
        ]
        
        med_summary_table = Table(med_summary_data, colWidths=[2 * inch, 2 * inch, 2 * inch])
        med_summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, 1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#334155')),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, 1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(med_summary_table)
        story.append(Spacer(1, 0.2 * inch))
        
        # Medication Table
        if medications.exists():
            med_data = [
                ['Medication Name', 'Dosage (mg)', 'Frequency', 'Category', 'Date Added', 'Active', 'Notes']
            ]
            
            for med in medications:
                med_data.append([
                    med.name,
                    str(med.dosage_amount_mg),
                    med.dosage_frequency,
                    med.category,
                    med.last_refill.strftime('%b %d, %Y'),
                    '✓' if med.active else '✗',
                    med.medication_more or ''
                ])
            
            med_table = Table(med_data, colWidths=[1.5 * inch, 0.9 * inch, 1 * inch, 1.2 * inch, 0.9 * inch, 0.5 * inch, 1.5 * inch])
            med_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#005fb8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#334155')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(med_table)
        else:
            story.append(Paragraph("No medications found in your account.", normal_style))
        
        story.append(Spacer(1, 0.3 * inch))
        
        # ==================== INTERACTION HISTORY SECTION ====================
        story.append(Paragraph("2. Interaction History", heading_style))
        
        # History Summary
        total_history = len(history)
        severity_counts = {}
        for item in history:
            severity = item.interaction.severity.lower()
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        high = severity_counts.get('high', 0)
        moderate = severity_counts.get('moderate', 0)
        low = severity_counts.get('low', 0)
        
        history_summary_data = [
            ['Total Interactions', 'High Risk', 'Moderate Risk', 'Low Risk'],
            [str(total_history), str(high), str(moderate), str(low)]
        ]
        
        history_summary_table = Table(history_summary_data, colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
        history_summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, 1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#334155')),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, 1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(history_summary_table)
        story.append(Spacer(1, 0.2 * inch))
        
        # History Table with FULL Description (no truncation)
        if history.exists():
            hist_data = [
                ['Date', 'Time', 'Drug 1', 'Drug 2', 'Severity', 'Description']
            ]
            
            for item in history[:50]:
                hist_data.append([
                    item.date_time.strftime('%Y-%m-%d'),
                    item.date_time.strftime('%H:%M'),
                    item.interaction.first_drug.common_name,
                    item.interaction.second_drug.common_name,
                    item.interaction.severity.upper(),
                    item.interaction.description or 'No description available.'
                ])
            
            if len(history) > 50:
                hist_data.append(['...', '...', f'{len(history) - 50} more records', '...', '...', '...'])
            
            # Use Paragraph for description to handle long text and auto-wrap
            hist_table = Table(hist_data, colWidths=[0.9 * inch, 0.6 * inch, 1.2 * inch, 1.2 * inch, 0.7 * inch, 2.5 * inch])
            hist_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#005fb8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#334155')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(hist_table)
        else:
            story.append(Paragraph("No interaction history found.", normal_style))
        
        # ==================== DISCLAIMER ====================
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#94a3b8'),
            alignment=TA_CENTER,
            spaceAfter=6
        )
        
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph(
            "This document contains sensitive medical information. Please handle with care.",
            disclaimer_style
        ))
        story.append(Paragraph(
            "This information is for educational purposes. Always consult a professional physician before consuming any medication.",
            disclaimer_style
        ))
        story.append(Paragraph(
            f"Generated by MediSafe • {datetime.now().strftime('%B %d, %Y')}",
            disclaimer_style
        ))
        
        # Build PDF
        doc.build(story)
        
        pdf_data = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(content_type='application/pdf')
        filename = f"complete_export_{user.full_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write(pdf_data)
        return response
        
    except Exception as e:
        print(f"Error exporting combined PDF: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Failed to generate export'}, status=500)


# ========== HISTORY PDF EXPORT ==========
def export_history_pdf(request):
    try:
        user = helpers.getUserFromSession(request.session)
        if user is None:
            return JsonResponse({'error': 'User not authenticated'}, status=401)
        
        history = models.UserHistory.objects.filter(
            user=user
        ).select_related(
            'interaction',
            'interaction__first_drug',
            'interaction__second_drug'
        )
        
        # Get severity counts for summary
        severity_counts = {}
        for item in history:
            severity = item.interaction.severity.lower()
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#005fb8'),
            alignment=TA_CENTER,
            spaceAfter=10
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#64748b'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=8,
            spaceBefore=10
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#334155'),
            spaceAfter=4
        )
        
        story = []
        
        # Header
        story.append(Paragraph("MediSafe Interaction History", title_style))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
        story.append(Paragraph(f"<b>Patient:</b> {user.full_name} | <b>Email:</b> {user.email}", normal_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Summary Section
        story.append(Paragraph("Summary", heading_style))
        
        total = len(history)
        high = severity_counts.get('high', 0)
        moderate = severity_counts.get('moderate', 0)
        low = severity_counts.get('low', 0)
        
        summary_data = [
            ['Total Interactions', 'High Risk', 'Moderate Risk', 'Low Risk'],
            [str(total), str(high), str(moderate), str(low)]
        ]
        
        summary_table = Table(summary_data, colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, 1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#334155')),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, 1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3 * inch))
        
        # History Table with FULL Description (no truncation)
        if history.exists():
            story.append(Paragraph("All Interaction Records", heading_style))
            
            hist_data = [
                ['Date', 'Time', 'Drug 1', 'Drug 2', 'Severity', 'Description']
            ]
            
            for item in history[:50]:
                hist_data.append([
                    item.date_time.strftime('%Y-%m-%d'),
                    item.date_time.strftime('%H:%M'),
                    item.interaction.first_drug.common_name,
                    item.interaction.second_drug.common_name,
                    item.interaction.severity.upper(),
                    item.interaction.description or 'No description available.'
                ])
            
            if len(history) > 50:
                hist_data.append(['...', '...', f'{len(history) - 50} more records', '...', '...', '...'])
            
            hist_table = Table(hist_data, colWidths=[0.9 * inch, 0.6 * inch, 1.2 * inch, 1.2 * inch, 0.7 * inch, 2.5 * inch])
            hist_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#005fb8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#334155')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(hist_table)
        
        # Disclaimer
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#94a3b8'),
            alignment=TA_CENTER,
            spaceAfter=6
        )
        
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph(
            "This information is for educational purposes. Always consult a professional physician before consuming any medication.",
            disclaimer_style
        ))
        story.append(Paragraph(
            f"Generated by MediSafe • {datetime.now().strftime('%B %d, %Y')}",
            disclaimer_style
        ))
        
        doc.build(story)
        
        pdf_data = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(content_type='application/pdf')
        filename = f"interaction_history_{user.full_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write(pdf_data)
        return response
        
    except Exception as e:
        print(f"Error exporting history PDF: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Failed to generate export'}, status=500)


# ========== SINGLE INTERACTION PDF EXPORT ==========
def export_interaction_pdf(request, history_id):
    try:
        user = helpers.getUserFromSession(request.session)
        if user is None:
            return JsonResponse({'error': 'User not authenticated'}, status=401)
        
        history_entry = models.UserHistory.objects.select_related(
            'interaction',
            'interaction__first_drug',
            'interaction__second_drug'
        ).get(
            user=user,
            id=history_id
        )
        
        interaction = history_entry.interaction
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor('#005fb8'),
            alignment=TA_CENTER,
            spaceAfter=10
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#64748b'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=6,
            spaceBefore=10
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#334155'),
            spaceAfter=4
        )
        
        story = []
        
        # Header
        story.append(Paragraph("Drug Interaction Report", title_style))
        story.append(Paragraph(f"Report #{history_entry.id} • {history_entry.date_time.strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Patient Info
        story.append(Paragraph(f"<b>Patient:</b> {user.full_name} | <b>Email:</b> {user.email} | <b>Report ID:</b> #{history_entry.id}", normal_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Drug Information
        story.append(Paragraph("Medications Analyzed", heading_style))
        
        drug_data = [
            ['Drug Name', 'DrugBank ID'],
            [interaction.first_drug.common_name, interaction.first_drug.drug_bank_id or 'N/A'],
            [interaction.second_drug.common_name, interaction.second_drug.drug_bank_id or 'N/A']
        ]
        
        drug_table = Table(drug_data, colWidths=[3 * inch, 3 * inch])
        drug_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#005fb8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#334155')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(drug_table)
        story.append(Spacer(1, 0.3 * inch))
        
        # Severity (with color coding)
        severity_colors = {
            'high': colors.HexColor('#dc2626'),
            'moderate': colors.HexColor('#f59e0b'),
            'low': colors.HexColor('#16a34a')
        }
        severity_color = severity_colors.get(interaction.severity.lower(), colors.HexColor('#64748b'))
        
        severity_style = ParagraphStyle(
            'Severity',
            parent=styles['Normal'],
            fontSize=14,
            textColor=severity_color,
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        story.append(Paragraph(f"Severity Level: {interaction.severity.upper()}", severity_style))
        story.append(Spacer(1, 0.1 * inch))
        
        # Description
        story.append(Paragraph("Interaction Description", heading_style))
        story.append(Paragraph(interaction.description or 'No description available.', normal_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Disclaimer
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#94a3b8'),
            alignment=TA_CENTER,
            spaceAfter=6
        )
        
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph(
            "This information is for educational purposes. Always consult a professional physician before consuming any medication.",
            disclaimer_style
        ))
        story.append(Paragraph(
            f"Generated by MediSafe • {datetime.now().strftime('%B %d, %Y')}",
            disclaimer_style
        ))
        
        doc.build(story)
        
        pdf_data = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(content_type='application/pdf')
        filename = f"interaction_report_{history_entry.id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write(pdf_data)
        return response
        
    except models.UserHistory.DoesNotExist:
        return JsonResponse({'error': 'Report not found'}, status=404)
    except Exception as e:
        print(f"Error exporting interaction PDF: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Failed to generate PDF'}, status=500)


# ========== HISTORY CSV EXPORT ==========
def export_history_csv(request):
    try:
        user = helpers.getUserFromSession(request.session)
        if user is None:
            return JsonResponse({'error': 'User not authenticated'}, status=401)
        
        history = models.UserHistory.objects.filter(
            user=user
        ).select_related(
            'interaction',
            'interaction__first_drug',
            'interaction__second_drug'
        )
        
        response = HttpResponse(content_type='text/csv')
        filename = f"interaction_history_{user.full_name}_{timezone.now()}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response, quoting=csv.QUOTE_ALL)
        
        writer.writerow([
            'Date Checked',
            'Time',
            'Drug 1',
            'Drug 2',
            'Severity',
            'Description'
        ])
        
        for item in history:
            writer.writerow([
                item.date_time.strftime('%Y-%m-%d'),
                item.date_time.strftime('%H:%M'),
                item.interaction.first_drug.common_name,
                item.interaction.second_drug.common_name,
                item.interaction.severity,
                item.interaction.description or ''
            ])
        
        return response
        
    except Exception as e:
        print(f"Error exporting history CSV: {e}")
        return JsonResponse({'error': 'Failed to export data'}, status=500)