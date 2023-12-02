import mysql.connector
import pathlib
from decouple import config

BASE_DIR = pathlib.Path(__file__).resolve().parent

class ConnectionPool(object):
    _dbconfig = None
    pool_name = 'bpool'
    _dbpool = None
    connections = []
    env = ''
    def __init__(self, env: str = 'dev'):
        self.env = env
        self.establish_pool()
    
    @property
    def db_config(self):
        if self._dbconfig is not None:
            return self._dbconfig
        
        return {
            "database": config('DB_NAME'),
            "host": config('DB_HOST'),
            "port": config('DB_PORT'),
            "username": config('DB_USERNAME'),
            "password": config('DB_PASSWORD')
        }
    
    def establish_pool(self) -> None:
        if self._dbpool is not None:
            return None

        self._dbpool = mysql.connector.pooling.MySQLConnectionPool(pool_name = self.pool_name,
                                                    pool_size = 3,
                                                    **self.db_config)
        return None
    
    def get_connection(self):
        return self._dbpool.get_connection()
