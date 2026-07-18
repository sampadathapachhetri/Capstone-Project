from django.contrib import admin
from MediSafe.models import Users
from MediSafe.models import UserProfile
from MediSafe.models import UserMedications
from MediSafe.models import OAuthAccount
from MediSafe.models import Drug_Interactions
from MediSafe.models import UserHistory
from MediSafe.models import OTP

admin.site.register(Users)
admin.site.register(UserProfile)
admin.site.register(UserMedications)
admin.site.register(OAuthAccount)
# admin.site.register(Drug_Interactions)
admin.site.register(UserHistory)
admin.site.register(OTP)
# Register your models here.
