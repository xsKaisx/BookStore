import traceback
from django.shortcuts import render
from django.db import transaction

from rest_framework.viewsets import ViewSet
from rest_framework.request import Request
from rest_framework.decorators import action
from rest_framework import serializers
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.utils import translate_validation

from lib.common.book_lib import data_serialize_class, log
from lib.common.filters import BookFilter
from lib.common.responses import helper_response

from . import models, serializers
# Create your views here.

class PublicView(ViewSet):
    authentication_classes = []
    permission_classes = []

    @action(methods = ['get'], detail = False)
    def get_books(self, request: Request, *args, **kwargs):
        book_obj = models.Book.objects.all()
        book_qs = BookFilter(request.GET, queryset=book_obj)
        if not book_qs.is_valid():
            raise translate_validation(book_qs.errors)
        book_data = serializers.BookModelSerializer(book_qs.qs, many = True)
        return helper_response.success(data = book_data.data)
    

    action(methods = ['get'], detail = False)
    def get_book_info(self, request: Request, *args, **kwargs):
        try:
            book_qs = models.Book.objects.get(pk = request.query_params['book_id'])
            book_detail_data = serializers.BookModelSerializer(instance = book_qs, context={'request': request}).data
            return helper_response.success(data = book_detail_data)
        except Exception as e:
            tb = traceback.format_exc()
            log.error(f'Hitting exception {e} while trying to get tournament\'s brackets. {tb}')
            return helper_response.failed(message = str(e))

class BookView(ViewSet):

    action(methods = ['post'], detail = False)
    @data_serialize_class(serializers.BookModelSerializer)
    def add_book(self, request: Request, *args, **kwargs):
        try:
            log.info(f'{request.user = }')
            with transaction.atomic():
                book = models.Book.objects.create(
                    author = kwargs['initial_valid_data']['author'],
                    title = kwargs['initial_valid_data']['title'],
                    publish_date = kwargs['initial_valid_data']['publish_date'],
                    isbn = kwargs['initial_valid_data']['isbn'],
                    price = kwargs['initial_valid_data']['price'],
                    available = kwargs['initial_valid_data']['available']
                )
                book_data = serializers.BookModelSerializer(instance = book)
                return helper_response.created(data = book_data.data)
        except Exception as e:
            tb = traceback.format_exc()
            log.error(f'Hitting exception {e} while trying to handle atomic transaction. {tb}')
            return helper_response.failed(message='Could not add new book')
        

    action(methods = ['post'], detail = False)
    @data_serialize_class(serializers.UpdateBookModelSerializer)
    def update_book(self, request: Request, *args, **kwargs):
        book = models.Book.objects.get(pk = kwargs['initial_valid_data']['book_id'])
        log.info(book.title)
        if kwargs['initial_valid_data'].get('author') is not None:
            book.author = kwargs['initial_valid_data']['author']
        if kwargs['initial_valid_data'].get('title') is not None:
            book.title = kwargs['initial_valid_data']['title'] 
        if kwargs['initial_valid_data'].get('book_cover') is not None:
            book.book_cover =kwargs['initial_valid_data']['book_cover']
        if kwargs['initial_valid_data'].get('publish_date') is not None:
            book.publish_date = kwargs['initial_valid_data']['publish_date'] 
        if kwargs['initial_valid_data'].get('isbn') is not None:
            book.isbn = kwargs['initial_valid_data']['isbn'] 
        if kwargs['initial_valid_data'].get('price') is not None:
            book.price = kwargs['initial_valid_data']['price'] 
        if kwargs['initial_valid_data'].get('available') is not None:
            book.available = kwargs['initial_valid_data']['available']  

        try:
            book.save()
            book.refresh_from_db()
            log.info(f'{book.book_cover.path}')
            return helper_response.success(message = 'updated')
        except Exception as e:
            tb = traceback.format_exc()
            log.error(f'Hitting exception {e} while trying to save book model. {tb}')
            return helper_response.failed() 
    action(methods = ['post'], detail = False)
    @data_serialize_class(serializers.DeleteBookModelSerializer)
    def delete_book(self, request: Request, *args, **kwargs):
        book = models.Book.objects.get(pk = kwargs['initial_valid_data']['book_id'])
        try:
            book.delete()
            return helper_response.success(message = 'Deleted!')
        except Exception as e:
            log.error(f'Hitting exception {e} while trying to delete book model.')
            return helper_response.failed(message = 'Could not delete book!')