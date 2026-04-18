from django.contrib import admin
from MediSafe.models import Users
from MediSafe.models import UserProfile
from MediSafe.models import UserMedications

admin.site.register(Users)
admin.site.register(UserProfile)
admin.site.register(UserMedications)
# Register your models here.
