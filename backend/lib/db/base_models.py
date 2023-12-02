from django.db import models as default_models
from uuid import uuid4

def generate_id() -> str:
    unique_key = str(uuid4())
    unique_key = unique_key.replace('-', '')
    return unique_key


class BaseSQLModel(default_models.Model):
    id = default_models.CharField(primary_key=True, max_length=255, default=generate_id)
    created = default_models.DateTimeField(auto_now=False, auto_now_add=True)
    last_updated = default_models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        ordering = ['-created']
        abstract = True
