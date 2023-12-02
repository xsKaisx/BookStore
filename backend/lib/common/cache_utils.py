import functools
import re
from typing import Any
from django.core.cache import caches
from django_redis.cache import RedisCache
from django.conf import settings

class BaseCacheUtils:
    store = None

    @classmethod
    def __str__(cls, *args, **kwargs):
        return f'BaseCacheUtils_type_${cls.store.__name__}'
    
    @classmethod
    def create_or_update_cache(cls, cache_key : str, value : dict, replace = False) -> dict:
        """
        create or update a cache data which is in key:value pair format. 
        returns the cache data
        """
        current_cache_data = cls.store.get(cache_key, None)
        if current_cache_data is not None and not replace:
            raise ValueError(f'could not create cache_key {cache_key} because it already exists and argument \"replace\" was set to False')

        if isinstance(current_cache_data, dict) and replace:
            new_value = {
                **current_cache_data,
                **value
            }
            cls.store.set(cache_key, new_value, timeout=settings.CACHE_MIDDLEWARE_SECONDS)
        else:
            cls.store.set(cache_key, {}, timeout=settings.CACHE_MIDDLEWARE_SECONDS)

        return cls.store.get(cache_key)
    
    def require_cache_key_exists(func):
        functools.wraps(func)
        def wrapper(cls, cache_key, *args, **kwargs):
            # find cache
            current_cache_data = cls.store.get(cache_key, None)
            if current_cache_data is None:
                raise ValueError(f'could not find cache_key at id ({cache_key}) in {cls.__str__()}')
            
            kwargs["current_cache_data"] = current_cache_data
            return func(cls, cache_key, *args, **kwargs)
        return wrapper

    @classmethod
    @require_cache_key_exists
    def add_or_set_key(cls, cache_key: str, key_path : str, key_value: Any, replace = False, **kwargs):
        """
        key_path is defined as dotted path such as a.b.c.d to describe a nested key
        return latest updated cache data
        """
        # find cache
        current_cache_data = kwargs["current_cache_data"]  # already prevent if could not find cache data on decorator

        if not isinstance(key_path, str):
            raise ValueError('Argument \"key_path\" must be string')
        if key_path == '' or bool(re.search(' ', key_path)):
            raise ValueError('Argument \"key_path\" must have characters and shall not contain space')

        splitted_keys = key_path.split('.')
        if len(splitted_keys) == 1:
            # no nested key
            if splitted_keys[0] in current_cache_data and not replace:
                raise ValueError(f'Could not add key because found key {splitted_keys[0]} in current_cache_data but replace arg is False.')
            
            current_cache_data.update({splitted_keys[0]: key_value})
            cls.store.set(cache_key, current_cache_data, timeout=settings.CACHE_MIDDLEWARE_SECONDS)

            return  cls.store.get(cache_key)
        else:
            # nested key
            access_path_str = [f"[\"{key_name}\"]" for key_name in splitted_keys]
            access_path_str = "".join(access_path_str)
            try:
                check_key_exists = eval(f"current_cache_data{access_path_str}")
            except KeyError:
                check_key_exists = None
            except Exception as e:
                raise ValueError(f'Hitting exception {e} :: when trying to check key exist at current_cache_data{access_path_str}')

            if check_key_exists != None and not replace:
                raise ValueError(f'could not add key because found key {access_path_str} in current_cache_data but replace arg is False')

            # create key in nested
            check_nested = "current_cache_data"
            for k in splitted_keys:
                check_nested += f"[\"{k}\"]"
                try:
                    check_ = eval(check_nested)
                    pass
                except:  # noqa: E722
                    create_ = check_nested + "={}"
                    try:
                        exec(create_)
                    except Exception as e:
                        print(f'current_cache_data (type: {type(current_cache_data)}):\n{current_cache_data}\n----\n')
                        raise ValueError(f'Hitting exception {e} when trying to create nested key {create_}')

            assign_value = f'{check_nested}={key_value}'
            try:
                exec(assign_value)
            except Exception as e:
                raise ValueError(f'Hitting exception {e} when trying to assign key_value arg to key: {assign_value}')
            
        cls.store.set(cache_key, current_cache_data, timeout=settings.CACHE_MIDDLEWARE_SECONDS)
        return cls.store.get(cache_key)
    
    @classmethod
    @require_cache_key_exists
    def delete_key(cls, cache_key: str, key_path: str, **kwargs):
        """
        delete key
        returns True / Exception
        """
        current_cache_data = kwargs.get('current_cache_data')

        if not isinstance(key_path, str):
            raise ValueError('key_path arg must be string')
        if key_path == '' or bool(re.search(' ', key_path)):
            raise ValueError('key_path arg must have characters and shall not contain space')


        splitted_keys = key_path.split('.')
        if len(splitted_keys) == 1:
            del current_cache_data[splitted_keys[0]]
        else:
            # nested key
            access_path_str = [f"[\"{key_name}\"]" for key_name in splitted_keys]
            access_path_str = "".join(access_path_str)
            try:
                statement_str = f"current_cache_data{access_path_str}"
                check_key_exists = eval(statement_str)
                exec(f'del {statement_str}')

            except Exception as e:
                raise ValueError(f'Hitting exception {e} :: when trying to check key exist at current_cache_data{access_path_str}')

        cls.store.set(cache_key, current_cache_data, timeout=settings.CACHE_MIDDLEWARE_SECONDS)
        return True

    @classmethod
    @require_cache_key_exists
    def get_key(cls, cache_key: str, key_path:str, **kwargs):
        current_cache_data = kwargs.get('current_cache_data')

        if not isinstance(key_path, str):
            raise ValueError('key_path arg must be string')
        if key_path == '' or bool(re.search(' ', key_path)):
            raise ValueError('key_path arg must have characters and shall not contain space')

        splitted_keys = key_path.split('.')
        if len(splitted_keys) == 1:
            return current_cache_data[splitted_keys[0]]
        else:
            # nested key
            access_path_str = [f"[\"{key_name}\"]" for key_name in splitted_keys]
            access_path_str = "".join(access_path_str)
            try:
                statement_str = f"current_cache_data{access_path_str}"
                key_value = eval(statement_str)
                return key_value

            except Exception as e:
                raise ValueError(f'Hitting exception {e} :: when trying to check key exist at current_cache_data{access_path_str}')
    
    def to_cache_key(self, session_id:str):
        return settings.CACHE_KEY_PREFIX + session_id

class RedisCacheUtils(BaseCacheUtils):
    store : RedisCache = caches["default"]
