import functools
import re
import logging
from django.utils import timezone
from django.conf import settings
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.request import Request

from .responses import helper_response
log = logging.getLogger("mt_loader")
def data_serialize_class(data_serializer_class: object):
    def decorator(func):
        @functools.wraps(func)
        def __wrapper__(self, request: Request, *args, **kwargs):
            requested_data = request.data
            requested_serializer: serializers.Serializer = data_serializer_class(data = requested_data)
            if not requested_serializer.is_valid():
                return helper_response.failed(message=requested_serializer.error_messages, data = requested_serializer.errors)
            valid_data = requested_serializer.validated_data

            kwargs['initial_serializer'] = requested_serializer
            kwargs['initial_valid_data'] = valid_data
            
            return func(self, request, *args, **kwargs)
        return __wrapper__
    return decorator

def set_cookie(response: Response, key, value, httponly: bool = False, path = '/') -> None:
    response.set_cookie(
        key = key,
        value = value,
        max_age=settings.SESSION_COOKIE_AGE,
        expires = timezone.now() + timezone.timedelta(seconds=settings.SESSION_COOKIE_AGE),
        path = path,
        domain = settings.SESSION_COOKIE_DOMAIN or  None,
        httponly=httponly,
        samesite=settings.SESSION_COOKIE_SAMESITE,
        secure=settings.SESSION_COOKIE_SECURE
    )

def validate_password_strong(password: str):
    contain_uppercase_letters = re.compile('[A-Z]')
    contain_numbers = re.compile('\d')
    contain_special_chars = re.compile('\W')

    if ((len(re.findall(contain_uppercase_letters, password)) > 0) and
        (len(re.findall(contain_numbers, password)) > 0) and
        (len(re.findall(contain_special_chars, password)) > 0)):
        return True
    
    return False