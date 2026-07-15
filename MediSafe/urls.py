from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from . import views
urlpatterns=[
    path('',view=views.index,name='index'),
    path('login/',view=views.login,name='login'),
    path('register/',view=views.register,name='register'),
    path('resetAccount/',views.resetPassword,name="reset_password"),
    path('sub/dashboard/',view=views.dashboard,name='dashboard'),
    path('sub/drugcheck/',view=views.drugCheck,name='drug_check'),
    path('sub/history',view=views.history,name="history"),
    path('sub/medications',view=views.medications,name='medications'),
    path('sub/settings',view=views.settingsView,name="settings"),
    path('sub/addmedications',view=views.addMedications,name="add_medications"),
    path('sub/intanalysis/',view=views.intAnalysis,name="int_analysis"),
    path('logout/',view=views.logout,name='logout'),
    path('delete_medication/<int:medicationId>',view=views.deleteMedication,name='delete_medication'),
    path('delete_medication/',view=views.deleteMedication,name='delete_medication'),
    path("api/checkdrug/",view=views.validateDrug,name="check_drug"),
    path("api/extract-name",view=views.extractName,name="ocr_upload"),
    path('auth/github/',view=views.github_login,name='github_login'),
    path('auth/github/callback/',view=views.github_callback),
    path('report/<int:history_id>/', views.report_detail, name='report_detail'), 
    path('switch_status/<int:medicationId>',view=views.switchStatusMedication,name="switch_status"),
    path("api/requestotp",view=views.requestOTP,name="request_otp"),
    path("api/requestPassReset",view=views.requestResetPassword,name="request_pass_reset"),
    path("delete_account/",view=views.deleteAccount,name="remove_account")
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)