import traceback
import json
import sys
import pathlib
from termcolor import colored
from utils.config import config
from utils.helper import read_yaml
from utils.sql_generator import SQLGenerator
# from utils.sql_generator import SQLGenerator

BASE_DIR = pathlib.Path(__file__).resolve().parent

def validate_data(data: dict):
    if data.get('id') is None:
        raise KeyError('data must have key id')

def record_exists(cursor, record_id, table_name: str) -> bool:
    cursor.execute(f'select count(id) from {table_name} where id = %s', params=(record_id, ))
    # check if record exists
    ret = cursor.fetchall()
    return ret[0].get("count(id)") != 0


def run_data(cursor, con, args, environment: str):
    for table_path in config.get('tables'):
        print(colored(f'(*) Running at table: {table_path}', 'magenta'))
        table_data = read_yaml(BASE_DIR / table_path)
        
        insert_sql = SQLGenerator.generate_insert_sql(table_data)
        update_sql = SQLGenerator.generate_update_sql(table_data)
        print(''.rjust(4) + colored(f'Adding master data to table {table_data["table-name"]}...', 'dark_grey', 'on_green'))
       
        insert_values = []  # sql values for insert :: list of tuples
        insert_records = [] # list of (<table_name>, <record_id>, <record_data>)
        update_values = []  # sql values for update :: list of tuples
        update_records = [] # list of (<table_name>, <record_id>, <record_data>)
        for data in table_data.get("data"):
            print(data)
            validate_data(data)
            data['publish_date'] = data['publish_date'].isoformat()
            if record_exists(cursor, data["id"], table_data["table-name"]):
                if not args.update:
                    print(''.rjust(8) + colored(f'(=) Record {data["id"]} already exists.', 'light_grey'))
                else:
                    print(''.rjust(8) + colored(f'(#) Updating existing record {data["id"]}', color='cyan'))
                    next_data = SQLGenerator.generate_next_record_sql(data, 'update', environment)
                    update_records.append((table_data['table-name'], data['id'], json.dumps(data, indent=4)))
                    update_values.append(next_data)
            else:
                next_data = SQLGenerator.generate_next_record_sql(data, 'insert', environment)
                insert_records.append((table_data['table-name'], data['id'], json.dumps(data, indent=4)))
                insert_values.append(next_data)

        try:
            cursor.executemany(update_sql, update_values)
            con._cnx.commit()
            cursor.executemany(insert_sql, insert_values)
            con._cnx.commit()

            for arec_table_name, arec_id, arec_data in insert_records:
                print(''.rjust(8) + colored(f'(+) Added record {arec_id}', 'green'))
            for arec_table_name, arec_id, arec_data in update_records:
                print(''.rjust(8) + colored(f'(+-) Updated record {arec_id}', 'green'))

        except Exception as e:
            tb = traceback.format_exc()
            print(colored(f'\nHitting exception {e} while trying to execute SQL. {tb}', 'red'))
            sys.exit(colored('SQL Execution Error. Check logs for failures', 'white', 'on_red'))
