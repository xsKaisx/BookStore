
import django_filters
from apps.models.models import Book

class BookFilter(django_filters.FilterSet):
    class Meta:
        model = Book
        fields = ['author', 'title', 'publish_date']