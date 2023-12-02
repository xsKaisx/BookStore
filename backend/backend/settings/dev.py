from .base import *


DEFAULT_FILE_STORAGE = 'backend.storages.storage_backend.BookStaticStorage'
# STATICFILES_STORAGE = 'backend.storages.storage_backend.BookStaticStorage'
# STATIC_URL = 'http://127.0.0.1:8000/static/'


MIDDLEWARE_ALIAS = 'default'  # using cache for middleware (talking to db)
CACHE_MIDDLEWARE_SECONDS = 1209600  # 2 weeks
CACHE_MIDDLEWARE_KEY_PREFIX = ''    # only when the cache is shared accross multiple sites

SESSION_CACHE_ALIAS = "default"   # using cache for session instead of default
SESSION_COOKIE_DOMAIN = host
SESSION_COOKIE_AGE = 1209600 # 2 weeks
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_NAME = "sessionid"
SESSION_COOKIE_PATH = "/"
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = False
SESSION_ENGINE = "django.contrib.sessions.backends.cache"

# Too add CSRF protection here
CORS_ALLOW_CREDENTIALS = True
CSRF_COOKIE_MASKED = True
CSRF_COOKIE_DOMAIN = host
CSRF_COOKIE_AGE = 1209600
# The reason for setting a long-lived expiration time is to avoid problems in the case of a user closing a browser 
# or bookmarking a page and then loading that page from a browser cache. Without persistent cookies, the form submission would fail in this case.

# Some browsers (specifically Internet Explorer) can disallow the use of persistent cookies or can have the indexes to the cookie jar corrupted on disk,
# thereby causing CSRF protection checks to (sometimes intermittently) fail. Change this setting to None to use session-based CSRF cookies, 
# which keep the cookies in-memory instead of on persistent storage.


CSRF_COOKIE_HTTP_ONLY = True
CSRF_COOKIE_NAME = "csrftoken"
CSRF_COOKIE_PATH = "/"
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"
CSRF_FAILURE_VIEW = "django.views.csrf.csrf_failure"
CSRF_USE_SESSIONS = False

REST_FRAMEWORK.update({
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.users.backend.CustomSessionAuthentication'
    ]
})

CACHES = {
    'default': {
        'BACKEND': "django_redis.cache.RedisCache",
        'LOCATION': 'redis://127.0.0.1:6379',
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },

}
