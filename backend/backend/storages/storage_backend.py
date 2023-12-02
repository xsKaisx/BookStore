from django.conf import settings
from django.core.files.storage import FileSystemStorage

class BookStaticStorage(FileSystemStorage):
    location = 'static'