from django.shortcuts import render,redirect
from django.http import Http404,HttpRequest,HttpResponse
from . import helpers
# Create your views here.
def index(request):
    return render(request=request,template_name="MediSafe/index.html", context={})

def login(request):
    return render(request=request,template_name="MediSafe/login.html",context={})

def register(request):
    if request.method=="POST":
        fullName=request.POST.get("fullname")
        email=request.POST.get("email")
        password=request.POST.get("password")
        confirmPassword=request.POST.get("confirm_password")
        if(password!=confirmPassword):
            pass
        if(len(password<8)):
            pass
        if(not helpers.isValidEmail(email=email)):
            pass
        if(len(fullName)<4):
            pass
        print(request.POST)
        return redirect("login")
    else:
        return render(request=request,template_name="MediSafe/register.html",context={})

def resetPassword(request):
    return render(request=request,template_name='MediSafe/resetAccount.html',context={})

def dashboard(request):
    return render(request=request,template_name='MediSafe/dashboard.html',context={})

def drugCheck(request):
    return render(request=request,template_name='MediSafe/drugCheck.html',context={})

def history(request):
    return render(request=request,template_name='MediSafe/history.html',context={})

def medications(request):
    return render(request=request,template_name='MediSafe/medications.html',context={})

def settings(request):
    return render(request=request,template_name='MediSafe/settings.html',context={})