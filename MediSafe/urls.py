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
    path("delete_account/",view=views.deleteAccount,name="remove_account"),
    path("api/gethistory/<int:historyId>",view=views.getInteractionHistorySingle,name="get_history"),
    path('api/history/', views.api_history_paginated, name='api_history_paginated'),
    path('api/medications/', views.api_medications, name='api_medications'),
    path('api/canAlertNot/', views.api_canGetAlertNotification, name='api_medications'),
    path('api/canReminderNot/', views.shouldPushReminderNotification, name='api_medications'),
    path('auth/google/', view=views.google_login, name='google_login'),
    path('auth/google/callback/', view=views.google_callback, name='google_callback'),
    
     path('validate_login/', views.validate_login, name='validate_login'),
    path('api/isTfaEnabled/', views.api_is_tfa_enabled, name='is_tfa_enabled'),
    path('export/combined/pdf/', views.export_combined_pdf, name='export_combined_pdf'),
    path('export/history/pdf/', views.export_history_pdf, name='export_history_pdf'),
    path('export/interaction/pdf/<int:history_id>/', views.export_interaction_pdf, name='export_interaction_pdf'),
    path('export/history/csv/', views.export_history_csv, name='export_history_csv'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)