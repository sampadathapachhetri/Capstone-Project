from django.db import models
import uuid
from . import helpers
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.db import transaction
# Create your models here.
class UserManager(models.Manager):
    def create_user_and_profile(self,email,full_name,password,):
        if not email or not helpers.isValidEmail(email=email):
            raise ValueError("Email invalid")
        with transaction.atomic():
            user=self.model(
                email=email,
                full_name=full_name,
                pass_hash=helpers.hash_password(password),
            )
            user.save(using=self._db)
            UserProfile.objects.get_or_create(user=user)
        return user
    def update_user_settings(self,user_id, email=None,full_name=None,safety_alerts=None,two_factor_auth=None,monthly_usage_reports=None):
        with transaction.atomic():
            user=self.get(id=user_id)
            updated_user_fields=[]
            if full_name is not None :
                user.full_name=full_name
                updated_user_fields.append("full_name")
            if email is not None and helpers.isValidEmail(email=email):
                user.email=email
                updated_user_fields.append("email")

            if updated_user_fields:
                user.save(update_fields=updated_user_fields)

            profile=user.profile
            updated_profile_fields=[]

            if safety_alerts is not None:
                profile.safety_alerts = safety_alerts
                updated_profile_fields.append('safety_alerts')
            
            if two_factor_auth is not None:
                profile.two_factor_auth = two_factor_auth
                updated_profile_fields.append('two_factor_auth')
            
            if monthly_usage_reports is not None:
                profile.monthly_usage_reports = monthly_usage_reports
                updated_profile_fields.append('monthly_usage_reports')
            
            if updated_profile_fields:
                profile.save(update_fields=updated_profile_fields)
            return user
                

class Users(models.Model):
    objects=UserManager()
    id=models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique Identifier for the user"
    )

    full_name=models.CharField(
        max_length=255,
        blank=False,
        help_text="User's Full Name"
    )

    pass_hash=models.CharField(
        max_length=255,
        blank=False,
        help_text="hashed password for user"
    )

    email=models.EmailField(
        max_length=255,
        unique=True,
        null=False,
        blank=False,
        error_messages={
            'unique':'A user with this email already exists.',
            'blank':"Email field cannot be empty",
            'null':"Email field cannot be null",
        },
        help_text="User's email"
    )

    created_at=models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the account was created"
    )

    last_logged_in_at=models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of user's last login"
    )
    class Meta:
        ordering=['-created_at']
        verbose_name='User'
        verbose_name_plural="Users"
        indexes=[
            models.Index(fields=['email'])
        ]
    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
    def update_last_login(self):
        from django.utils import timezone
        self.last_logged_in_at=timezone.now()
        self.save(update_fields=['last_logged_in_at'])

class UserProfile(models.Model):
    user=models.OneToOneField(
        Users,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='profile'
        )
    
    profile_image=models.ImageField(
        upload_to=helpers.get_profile_upload_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['jpg','jpeg','png'])]

    )

    two_factor_auth=models.BooleanField(
        default=False,
        help_text="2FA, enabled? "
    )
    safety_alerts=models.BooleanField(
        default=False,
        help_text="User's noti pred for high-priority safety alerts"
    )
    monthly_usage_reports=models.BooleanField(
        default=False,
        help_text="Noti Pref for monthly logs, probably mailed"
    )
    
    updated_at=models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name='User Profile'
        verbose_name_plural='User Profiles'

    def __str__(self):
        return f"Profile of {self.user.full_name}"



class UserMedications(models.Model):
    user=models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name="usersMedications",
        db_index=True
    )
    name=models.CharField(
        max_length=100,

    )
    dosage_amount_mg=models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=False
    )
    dosage_frequency=models.CharField(
        max_length=100,
    )
    last_refill=models.DateTimeField(
        auto_now_add=True,
    )
    active=models.BooleanField(
        default=True
    )
    category=models.CharField(
        max_length=100,
        default="UnIdentified"
    )

    class Meta:
        indexes=[
            models.Index(fields=['last_refill'])
        ]

