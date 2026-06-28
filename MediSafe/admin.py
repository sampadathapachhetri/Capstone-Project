from django.contrib import admin
from MediSafe.models import Users
from MediSafe.models import UserProfile
from MediSafe.models import UserMedications
from MediSafe.models import OAuthAccount

admin.site.register(Users)
admin.site.register(UserProfile)
admin.site.register(UserMedications)
admin.site.register(OAuthAccount)
# Register your models here.
