from django.urls import path,include
from . import views
urlpatterns=[
    path('',view=views.index,name='index'),
    path('login/',view=views.login,name='login'),
    path('register/',view=views.register,name='register'),
    path('reset password/',views.resetPassword,name="reset_password"),
    path('sub/dashboard/',view=views.dashboard,name='dashboard'),
    path('sub/drugcheck/',view=views.drugCheck,name='drug_check'),
    path('sub/history',view=views.history,name="history"),
    path('sub/medications',view=views.medications,name='medications'),
    path('sub/settings',view=views.settings,name="settings"),
    path('sub/addmedications',view=views.addMedications,name="add_medications"),
    path('sub/intanalysis',view=views.intAnalysis,name="int_analysis"),

]