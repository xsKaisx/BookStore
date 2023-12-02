import os
import pathlib
import argparse
from utils.db import ConnectionPool
from contextlib import closing

from _data import run_data

from dotenv import load_dotenv
load_dotenv()

parser = argparse.ArgumentParser(
    prog='Bookstore master data',
    description='Create/Update Master Data including updating/creating s3 artifacts if any'
)
parser.add_argument('--environment', '-env', action='store', choices=['dev', 'staging'], default='local', type=str, required=True, help='Name of the environment')
parser.add_argument('--update', '-u', action='store_true', required=False, help='Apply master data on existing DB records')
args, unknown_args = parser.parse_known_args()
print(args.__dict__)


BASE_DIR = pathlib.Path(__file__).resolve().parent
connection_pool = ConnectionPool(env=args.environment)


if __name__ == '__main__':
    with closing(connection_pool.get_connection()) as con:
        cursor = con._cnx.cursor(dictionary=True)
        run_data(cursor, con, args, args.environment)
