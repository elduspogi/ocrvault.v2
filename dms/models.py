from django.db import models
from django.contrib.auth.models import UserManager, AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from django.utils.text import slugify
import uuid
import os
from PIL import Image
from django.utils.timezone import now

"""
    GLOBAL FUNCTIONS
"""

def id_generator():
    return uuid.uuid4().hex.replace('-', '')[:26].upper()

# Create your models here.

"""
    USER MODEL
"""
class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("You have not provided a valid email address.")
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user
    
    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)
    
    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, password, **extra_fields)
    
class User(AbstractBaseUser, PermissionsMixin):
    id = models.CharField(max_length=26, primary_key=True, unique=True, null=False, blank=False)
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    image = models.ImageField(default='default_profile_pics/paio_default.jpg', upload_to='profile_pics/')
    # User Roles
    # Superadmin, Admin, Reviewer, Office Staff
    user_type = models.CharField(max_length=255, default='STAFF', blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    starred_documents = models.TextField(null=True, blank=True)
    starred_folders = models.TextField(default='', null=True, blank=True)
    is_changepass = models.BooleanField(default=False)
    password_reset_token = models.CharField(max_length=255, blank=True, null=True)
    password_reset_token_created_at = models.DateTimeField(blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=255, blank=True, null=True)
    email_token_created_at = models.DateTimeField(blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{ self.id } - { self.email }"

    def save(self, *args, **kwargs):
        if not self.id:
            # self.id = uuid.uuid4().hex.replace('-', '')[:26].upper()
            self.id = id_generator()

        if self.image and hasattr(self.image, 'path') and os.path.exists(self.image.path):
            img = Image.open(self.image.path)

            if img.height > 300 or img.width > 300:
                output_size = (300,300)
                img.thumbnail(output_size)
                img.save(self.image.path)
        super().save(*args, **kwargs)

"""

    FOLDER MODEL

"""
class Folder(models.Model):
    id = models.CharField(max_length=26, primary_key=True, unique=True)
    name = models.CharField(max_length=255, default='Untitled Folder')
    parent = models.ForeignKey('self', related_name='children', null=True, blank=True, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='folder_created_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='folder_updated_by')
    updated_at = models.DateTimeField(auto_now=True)
    # TYPE = [PUBLIC, PRIVATE]
    type = models.CharField(max_length=255, default='PUBLIC')
    kind = models.CharField(max_length=100, default='FOLDER')
    allowed_users = models.ManyToManyField(User, blank=True)
    is_deleted = models.BooleanField(default=False)
    is_reviewed = models.BooleanField(default=False)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.id}"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = id_generator()
        super().save(*args, **kwargs)
    
    def delete_folder_recursive(self):
        # Delete child folders recursively
        children = Folder.objects.filter(parent=self)
        for child in children:
            child.delete_folder_recursive()
        # Delete the current folder
        self.delete()

"""

    DOCUMENT MODEL

"""
from django.core.files.storage import default_storage

class Document(models.Model):
    id = models.CharField(max_length=26, primary_key=True, unique=True)
    title = models.CharField(max_length=255, default='Untitled Document')
    file = models.FileField(upload_to='documents/', null=True, blank=True)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField(max_length=20, default='PUBLIC', null=True, blank=True)
    kind = models.CharField(max_length=100, default='DOCUMENT')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_created_by', null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_updated_by', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    allowed_users = models.TextField(default='', null=True, blank=True)
    extracted_text = models.TextField(default='', null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=1)
    is_reviewed = models.BooleanField(default=False)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f'{self.id}'

    def delete(self, *args, **kwargs):
        for version in self.documentversion_set.all():
            if version.file:
                if default_storage.exists(version.file.name):
                    default_storage.delete(version.file.name)
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = id_generator()
        super().save(*args, **kwargs)

class DocumentVersion(models.Model):
    id = models.CharField(max_length=26, primary_key=True, unique=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(upload_to='versions/', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    version = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.id}'

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = id_generator()
        super().save(*args, **kwargs)

class ArchiveVersion(models.Model):
    id = models.CharField(max_length=26, primary_key=True, unique=True)
    file = models.FileField(upload_to='archives/', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.id}'

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = id_generator()
        super().save(*args, **kwargs)

class Notification(models.Model):
    id = models.CharField(max_length=26, primary_key=True, unique=True)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipient', null=True, blank=True)
    doer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doer', null=True, blank=True)
    type_id = models.CharField(max_length=26, null=True, blank=True)
    kind = models.CharField(max_length=100, null=True, blank=True)
    text = models.TextField(default='')
    created_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.id}'

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = id_generator()
        super().save(*args, **kwargs)

class ActivityLog(models.Model):
    id = models.CharField(max_length=26, primary_key=True, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    type_id = models.CharField(max_length=26, null=True, blank=True)
    kind = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)
    text = models.TextField(default='')
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.id}'

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = id_generator()
        super().save(*args, **kwargs)

class Report(models.Model):
    id = models.CharField(max_length=26, primary_key=True, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_by', null=True, blank=True)
    type_id = models.CharField(max_length=26, null=True, blank=True)
    kind = models.CharField(max_length=26, null=True, blank=True)
    type = models.CharField(max_length=255, null=True, blank=True)
    details = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verified_by', null=True, blank=True)

    def __str__(self):
        return f'{self.id}'

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = id_generator()
        super().save(*args, **kwargs)