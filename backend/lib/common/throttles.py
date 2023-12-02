from django.core.cache import caches
from django_redis.cache import RedisCache
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class CustomUserRateThrottle(UserRateThrottle):
    cache: RedisCache = caches["default"]

class CustomAnonRateThrottle(AnonRateThrottle):
    cache: RedisCache = caches["default"]