from django.shortcuts import render
from django.http import Http404,HttpRequest,HttpResponse
# Create your views here.
def index(request):
    return HttpResponse("HELLO")

def login(request):
    return HttpResponse("HELLO")
