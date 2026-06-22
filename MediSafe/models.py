from django.db import models
import uuid
from . import helpers
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.db import transaction,IntegrityError
# Create your models here.
class UserManager(models.Manager):
    def create_user_and_profile(self,email:str,full_name:str,password:str):
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
            if full_name=="":
                full_name=user.full_name
            if email=="":
                email=user.email
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
    def create_oauth_user_and_profile(self,full_name:str,provider:str,provider_user_id:str,access_token:str,provider_name,refresh_token=None,token_expires_at=None):
        with transaction.atomic():
            try: 
                acc=OAuthAccount.objects.get(
                    provider=provider,
                    provider_user_id=provider_user_id
                )
                user=Users.objects.get(id=acc.user.id)
            
            except (OAuthAccount.DoesNotExist, IntegrityError):
                    user=self.model(
                        full_name=full_name,
                        is_oauth_user=True
                    )
                    user.save(using=self._db)
                    UserProfile.objects.create(user=user)
                    acc=OAuthAccount.objects.create(
                        provider=provider,
                        provider_name=provider_name,
                        provider_user_id=provider_user_id,
                        access_token=access_token,
                        user=user,
                    )
            except Users.DoesNotExist:
                # user doesnot exist error, unexpected
                return
            acc.user = user
            acc.provider_name = provider_name
            acc.access_token = access_token
            acc.token_expires_at = token_expires_at
            acc.refresh_token = refresh_token
            acc.save()
        return user

class Users(models.Model):
    objects=UserManager()
    id=models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique Identifier for the user",
        db_index=True
    )

    full_name=models.CharField(
        max_length=255,
        blank=False,
        help_text="User's Full Name"
    )

    pass_hash=models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="hashed password for user"
    )

    email=models.EmailField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        error_messages={
            'unique':'A user with this email already exists.',
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
    is_oauth_user=models.BooleanField(
        default=False,
        help_text="Does user use OAuth for authentication?"
    )
    class Meta:
        indexes=[
            models.Index(fields=['email'])
        ]
    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
    def update_last_login(self):
        from django.utils import timezone
        self.last_logged_in_at=timezone.now()
        self.save(update_fields=['last_logged_in_at'])
    def has_password(self):
        return bool(self.pass_hash)

class OAuthAccount(models.Model):
    OAUTH_PROVIDERS=[
        ('google','Google'),
        ('github','GitHub')
    ]
    id=models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user=models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name="oauth_accounts",
        help_text="Reference to main user account"
    )
    provider=models.CharField(
        max_length=50,
        choices=OAUTH_PROVIDERS,
        help_text="OAuth provider name"
    )
    provider_user_id=models.CharField(
        max_length=255,
        help_text="User ID from the OAuth Provider"
    )
    access_token=models.TextField(
        help_text="OAuth access token"
    )
    refresh_token=models.TextField(
        blank=True,
        null=True,
        help_text="OAuth refresh token (if available)"
    )
    token_expires_at=models.DateTimeField(
        blank=True,
        null=True,
        help_text="Token expiration timestamp"
    )
    provider_name=models.CharField(
        max_length=255,
        help_text="Full name from OAuth Provider"
    )
    created_at=models.DateTimeField(
        auto_now_add=True,
        help_text="When the OAuth account was linked"
    )
    updated_at=models.DateTimeField(
        auto_now=True,
        help_text="Late updated at "
    )
    
    class Meta:
        unique_together=[
            ['provider','provider_user_id'],
        ]
        indexes=[
            models.Index(fields=['provider','provider_user_id']),
            models.Index(fields=['user','provider'])
        ]
    def __str__(self):
        return f"{self.user.email} - {self.provider}"
    
    def is_token_valid(self):
        from django.utils import timezone
        if self.token_expires_at:
            return self.token_expires_at>timezone.now()
        return True


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
        default="unknown"
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
    medication_more=models.TextField(
        blank=True,
        default=""
    )
    def __str__(self):
        return f"{self.name} , {self.dosage_amount_mg} , {self.dosage_frequency}"
    
    class Meta:
        indexes=[
            models.Index(fields=['user','last_refill'])
        ]
    
class Drug(models.Model):
    name=models.CharField(max_length=100,db_index=True,unique=True)
    smile_structure=models.CharField(max_length=100)
    drug_bank_id=models.CharField(max_length=50,unique=True,db_index=True)
    drug_synonym=models.CharField(max_length=100)
    def __str__(self):
        return f'{self.name}, {self.drug_synonym}'


class Severity(models.Model):
    level=models.CharField(max_length=20,unique=True)
    info=models.TextField()

class Drug_Interactions(models.Model):
    first_drug=models.ForeignKey(
        Drug,
        on_delete=models.CASCADE,
        related_name="first_drug"
    )
    second_drug=models.ForeignKey(
        Drug,
        on_delete=models.CASCADE,
        related_name="second_drug"
    )
    description=models.TextField()
    mechanism=models.TextField()
    recommendation=models.TextField()

    severity=models.ForeignKey(
        to=Severity,
        null=True,
        on_delete=models.SET_NULL,
    )
    class Meta:
        indexes=[
            models.Index(fields=['first_drug','second_drug'])
        ]

class UserHistory(models.Model):
    user=models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='history'
        
    )
    date_time=models.DateTimeField(
        auto_now_add=True,

    )
    interaction=models.ForeignKey(Drug_Interactions,on_delete=models.CASCADE,
                                  related_name='interaction')
    
    
    class Meta:
        ordering=['-date_time']
        indexes = [
        models.Index(fields=['user', '-date_time']),
    ]
    def __str__(self):
        return f"{self.date_time}"