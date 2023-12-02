from rest_framework.urls import path
from django.conf.urls.static import static
from django.conf import settings

from . import views
urlpatterns = [
    path('books/', views.PublicView.as_view({'get': 'get_books'}), name='get_books'),
    path('books/detail', views.PublicView.as_view({'get': 'get_book_info'}), name='book_detail'),
    path('books/create', views.BookView.as_view({'post': 'add_book'}), name='add_new_book'),
    path('books/update', views.BookView.as_view({'post': 'update_book'}), name='update_book'),
    path('books/delete', views.BookView.as_view({'post': 'delete_book'}), name='delete_book'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)