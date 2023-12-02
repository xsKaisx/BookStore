from django.db import models as default_models
from django.contrib import admin
from . import admin as AdminModel
from lib.db.base_models import BaseSQLModel
from lib.db.hooks import mysql_hook, MySQLAdminModel
from apps.users.models import UserProfile
from backend.storages import storage_backend
# Create your models here.

# class Author(BaseSQLModel):
#     profile = default_models.OneToOneField(to = UserProfile, on_delete=default_models.CASCADE, related_name='author_profile')

#     class Meta:
#         db_table = 'authors'
# mysql_hook.register(Author)
# admin.site.register(Author, MySQLAdminModel)

class Book(BaseSQLModel):
    author = default_models.CharField(max_length=255, null=True, blank=True, default=None)
    title = default_models.CharField(max_length=255, null=True, blank=True, default=None)
    book_cover = default_models.ImageField(max_length=255, null=True, blank=True, default=None, storage=storage_backend.BookStaticStorage)
    publish_date = default_models.DateField(null=True, blank=True, default=None)
    isbn = default_models.CharField(max_length=255, unique=True, null=True, blank=True, default=None)
    price = default_models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None)
    available = default_models.BooleanField(default=True, blank=True, null=True)
    

    class Meta:
        db_table = 'books'
mysql_hook.register(Book)
admin.site.register(Book, AdminModel.BookAdmin)