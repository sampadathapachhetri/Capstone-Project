from django.urls import path,include
from . import views
urlpatterns=[
    path('',view=views.index,name='index'),
    path('login/',view=views.login,name='login')
]