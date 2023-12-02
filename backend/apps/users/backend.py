import traceback
import os
from django.conf import settings

from rest_framework.authentication import BaseAuthentication
from rest_framework.request import Request

from lib.common.cache_utils import RedisCacheUtils
from lib.common.book_lib import log
from . import models

def get_cache_data(request_ssid: str):
    if request_ssid is None:
        log.debug("Could not recognize session id in request. Jumping to the next authentication class")
        return None

    request_cache_key = settings.CACHE_KEY_PREFIX + request_ssid
    cache_data = RedisCacheUtils().store.get(key = request_cache_key,default=None)
    return cache_data


class CustomSessionAuthentication(BaseAuthentication):
    def authenticate(self, request: Request, *args, **kwargs):
        log.info('start authenticating')
        log.debug('start authenticating debug')
        request_ssid = request._request.session.session_key
        cache_data = get_cache_data(request_ssid)
        if (cache_data is None):
            log.debug(f'Could not find cache_data by cache_key ${request_ssid}.')
            # return (AnonymousUser, None)
            return None
        if not isinstance(cache_data, dict):
            log.debug(f'Data from cache_key ${request_ssid} is not a dictionary.')
            # return (AnonymousUser, None)
            return None
        
        try:
            if "c_id" in cache_data:
                user : models.User = models.User.objects.get(pk=cache_data["c_id"])
            else:
                user : models.User = models.User.objects.get(pk=cache_data["_auth_user_id"])
        except Exception as e:
            tb = traceback.format_exc() 
            log.debug(f"Hitting exception {e} while trying to get 'c_id' or '_auth_user_id' in cache data. {tb}")
            return None

        return (user, request_ssid)