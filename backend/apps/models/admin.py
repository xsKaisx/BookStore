from django.contrib import admin

from lib.db.hooks import MySQLAdminModel
# Register your models here.

# class AuthorAdmin(MySQLAdminModel):
#     list_display =('username',)
#     ordering = ['username',]
    
class BookAdmin(MySQLAdminModel):
    list_display = ('title', 'publish_date',)
    ordering = ['title',]

    @admin.display(ordering='-title',description='Title')
    def username(self, obj):
        return obj.title
    
    @admin.display(ordering='-publish_date',description='Publish Date')
    def publish_date(self, obj):
        return obj.publish_date