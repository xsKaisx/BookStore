from django.contrib import admin
from django.db import models as default_models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from . import admin as AdminModel
from lib.db.base_models import BaseSQLModel
from lib.db.hooks import mysql_hook
from .managers import UserManager


# Create your models here.
LOGIN_METHOD = (
    ('EMAIL', 'email / password'),
    ('PHONENUMBER', 'phone number')
)
class User(AbstractBaseUser, PermissionsMixin, BaseSQLModel):
    username = default_models.CharField(max_length=255, unique=True)
    password = default_models.CharField(max_length=255, null=True, default=None)

    login_method = default_models.CharField(choices=LOGIN_METHOD, default='EMAIL', max_length=255)
    last_logged_in = default_models.DateTimeField(auto_now=True, auto_now_add=False)

    is_active = default_models.BooleanField(default=True)
    is_staff = default_models.BooleanField(default=False)
    is_superuser = default_models.BooleanField(default=False)
    is_admin = default_models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []
    
    objects: UserManager = UserManager()

    def __str__(self):
        return self.username
    
    class Meta:
        db_table = 'users'
mysql_hook.register(User)
admin.site.register(User, AdminModel.UserAdmin)

class UserProfile(BaseSQLModel):
    user = default_models.OneToOneField(to = User, on_delete=default_models.CASCADE, related_name='user_profile')
    first_name = default_models.CharField(max_length=255, blank=True, null=True, default=None)
    last_name = default_models.CharField(max_length=255, blank=True, null=True, default=None)

    email = default_models.EmailField(null = True, blank=True, default = None)
    phone = default_models.CharField(max_length = 20, null = True, blank = True, default = None)
    biography = default_models.CharField(max_length=255, null = True, blank = True, default = None)
    dob = default_models.DateField(null = True, blank=True, default = None)
    country = default_models.CharField(max_length = 100, null = True, blank=True, default = None)
    address = default_models.CharField(max_length = 255, null = True, blank=True, default = None)

    class Meta:
        db_table = 'user_profiles'
mysql_hook.register(UserProfile)
admin.site.register(UserProfile, AdminModel.UserProfileAdmin)