import inspect
from django.contrib import admin

class RouterHook:
    def __init__(self, db_name:str, app_labels = []):
        self.db_name = db_name
        self.route_app_labels = app_labels
        self.route_table_names = []
        self.route_model_names = []

    def register(self, model_class, *args, **kwargs):
        if not inspect.isclass(model_class):
            raise ValueError('RouterHook: argument \"model_class\" is not a class')
        
        self.route_table_names.append(model_class._meta.db_table)
        self.route_model_names.append(model_class._meta.model_name)

mysql_hook : RouterHook = RouterHook('default', ['users', 'models'])

### admin router
# https://docs.djangoproject.com/en/4.1/topics/db/multi-db/
class MultiDBAdminModel(admin.ModelAdmin):
    using = 'other'

    def save_model(self, request, obj, form, change):
        # Tell Django to save objects to the 'other' database.
        obj.save(using=self.using)

    def delete_model(self, request, obj):
        # Tell Django to delete objects from the 'other' database
        obj.delete(using=self.using)

    def get_queryset(self, request):
        # Tell Django to look for objects on the 'other' database.
        return super().get_queryset(request).using(self.using)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Tell Django to populate ForeignKey widgets using a query
        # on the 'other' database.
        return super().formfield_for_foreignkey(db_field, request, using=self.using, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Tell Django to populate ManyToMany widgets using a query
        # on the 'other' database.
        return super().formfield_for_manytomany(db_field, request, using=self.using, **kwargs)

class MySQLAdminModel(MultiDBAdminModel):
    using = 'default'