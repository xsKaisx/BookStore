import traceback
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.sessions.backends.cache import SessionStore
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes, throttle_classes
from rest_framework import parsers

from lib.common.responses import helper_response
from lib.common.book_lib import data_serialize_class, log, set_cookie
from lib.common.cache_utils import RedisCacheUtils
from . import serializers, models, backend
# Create your views here.

def handle_login_cookie(response: Response, user: models.User):
    new_session = SessionStore()
    new_session['c_id'] = user.id
    new_session.save()

    session_id = new_session.session_key
    log.info(f'{session_id =}')
    set_cookie(response, settings.SESSION_COOKIE_NAME, session_id, True)
    set_cookie(response, 'c_id', new_session.get('c_id'), True)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
@throttle_classes([])
def login_status(request: Request, *args, **kwargs):
    res = backend.CustomSessionAuthentication().authenticate(request)
    if res is None:
        return helper_response.success(data={'is_logged_in': False})
    else:
        return helper_response.success(data={'is_logged_in': True})

class SignUpView(ViewSet):  
    permission_classes = []
    authentication_classes = []
    @action(methods = ['post'], detail = False)
    @data_serialize_class(serializers.RegisterSerializer)
    def signup(self, request: Request,  *args, **kwargs):
        initial_valid_data = kwargs["initial_valid_data"]
        initial_serializer : serializers.RegisterSerializer = kwargs["initial_serializer"]

        try:
            user, profile = initial_serializer.create_user(initial_valid_data)
        except Exception as e:
            log.error(e)
            return helper_response.failed(message = "Could not create user. Check logs for failure.")
        
        res_data = serializers.UserModelSerializer(instance=  user).data
        return helper_response.created(data = res_data)
    
class AuthenticationView(ViewSet):
    permission_classes = []
    authentication_classes = []
    @action(methods = ['post'], detail = False)
    @data_serialize_class(serializers.LoginSerializer)
    def login(self, request: Request, *args, **kwargs):
        try:
            log.debug(f'{request._request.headers = }')
            # check user exists and password matched (authenticate user)
            user : models.User = authenticate(username = kwargs["initial_valid_data"]['username'], password = kwargs['initial_valid_data']['password'])
            if user is None or (not user.is_active):
                return helper_response.failed(message = 'Wrong username/password')
            
            profile: models.UserProfile = user.user_profile

            user_data = serializers.UserModelSerializer(instance=user).data
            user_profile_data = serializers.UserProfileModelSerializer(instance=profile).data

            res_data = {
                "user": {**user_data},
                "profile": {**user_profile_data}
            }
            api_response = helper_response.success(message = 'You are logged in', data = res_data)
            handle_login_cookie(api_response, user)
            return api_response
        except Exception as e:
            tb = traceback.format_exc()
            log.error(f'Hitting exception {e} while trying to handle logging. {tb}')
            return helper_response.failed(message = f'Hitting exception {e} while trying to handle logging. {tb}')
        
class AccountViews(ViewSet):
    parser_classes= [parsers.JSONParser, parsers.MultiPartParser, parsers.FileUploadParser]

    @action(methods = ['post'], detail = False)
    @throttle_classes([])
    def log_out(self, request: Request, *args, **kwargs):
        get_session = request._request.session
        log.info(f'session key: {get_session.session_key}')
        log.info(f'cache prefix: {settings.CACHE_KEY_PREFIX}')
        try:
            RedisCacheUtils.store.delete(str(settings.CACHE_KEY_PREFIX + get_session.session_key))
        except Exception as e:
            log.error(e)
            return helper_response.failed(message = str(e))
            
        return helper_response.success()
