from django.db import models
import uuid
from . import helpers
from django.utils import timezone
from django.core.validators import FileExtensionValidator
# Create your models here.

class Users(models.Model):
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
        db_table='users'
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

    updated_at=models.DateTimeField(auto_now=True)

    class Meta:
        db_table='user_profiles'
        verbose_name='User Profile'
        verbose_name_plural='User Profiles'

    def __str__(self):
        return f"Profile of {self.user.full_name}"