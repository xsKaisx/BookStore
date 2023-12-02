from django.contrib import admin
# from django.db import models
from lib.db.hooks import MySQLAdminModel
# Register your models here.

class UserAdmin(MySQLAdminModel):
    ordering = ['-created',]
    list_display = ('username', 'created',)

class UserProfileAdmin(MySQLAdminModel):
    date_hierarchy = 'created'
    list_display = ('username', 'first_name', 'last_name', 'created',)
    ordering = ['-created',]

    @admin.display(ordering='-username',description='Username')
    def username(self, obj):
        return obj.user.username