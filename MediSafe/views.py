from django.shortcuts import render,redirect
from django.http import Http404,HttpRequest,HttpResponse
from . import helpers,models
# Create your views here.
def index(request):
    context={}
    error={}
    message={}
    profile={}
    try:
        request.session['user_id']
        userId=request.session['user_id']
        try:
            user=models.Users.objects.get(id=userId)
            username=user.full_name
            profile["username"]=username
            shortName=username.split(" ")[0]+" " +username.split(" ")[1][0]+"."
            profile['username_short']=shortName
            context["profile"]=profile
            return render(request=request,template_name="MediSafe/index.html", context=context)
        except:
            return redirect("login")
    except:
        return redirect("login")

def login(request):
    context={}

    # Error K-V sample
    error={
        # "invalid_cred":"invalid email or password",
        # "empty_field":"The fields must not be empty",
        # "unknown":"Unknown Error occured",
    }
    if(request.method=="POST"):
        email=request.POST.get("email")
        if( not helpers.isValidEmail(email=email)):
            error["invalid_cred"]="Invalid email or password"
        password=request.POST.get("password")
        isRemember=request.POST.get("remember")
        # Function returns user id
        userId=authenticate(email=email,password=password)
        if(userId):
            request.session['user_id']=userId
            request.session.set_expiry(0)
            return redirect('index')
        else:
            error["invalid_cred"]='Invalid email or password'
    if(error):
        context["error"]=error
    return render(request=request,template_name="MediSafe/login.html",context=context)

def register(request):
    context={}

    # Error K-V sample
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
            newUser=models.Users.objects.create(
                full_name=fullName,
                email=email,
                pass_hash=helpers.hash_password(password))
            newUser.save()
            request.session['user_id']=f"{newUser.id}"
            request.session.set_expiry(0)
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
    return render(request=request,template_name='MediSafe/medications.html',context={})

def settings(request):
    return render(request=request,template_name='MediSafe/settings.html',context={})



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
