import re, copy, json, datetime, pytz

def validate_table(table: dict):
    if table.get('data') is None:
        raise KeyError('table must have key data')
    if table.get('table-name') is None:
        raise KeyError('table must have key table-name')

class SQLGenerator:
    url_pat = re.compile("url\(([\w\-_\.\/]*)\)")

    @classmethod
    def handle_string_field(cls, value, environment: str):
        # url_ret = re.match(cls.url_pat, value)
        # if bool(url_ret):
        #     img_key = upload_file_to_s3(url_ret.groups()[0], environment)
        #     return img_key
        return value
    
    @classmethod
    def handle_dict_field(cls, value, environment: str):
        copy_value = copy.deepcopy(value)
        # for sub_key, sub_value in value.items():
        #     if isinstance(sub_value, str):
        #         url_ret = re.match(cls.url_pat, sub_value)
        #         if bool(url_ret):
        #             img_key = upload_file_to_s3(url_ret.groups()[0], environment)
        #             copy_value[sub_key] = img_key
        #     else:
        #         pass
        return json.dumps(copy_value)
    
    @classmethod
    def generate_next_record_sql(cls, initial_data: dict, action: str, environment: str) -> dict:
        copy_initial_data = copy.deepcopy(initial_data)
        for key, value in initial_data.items():
            if isinstance(value, str):
                copy_initial_data[key] = cls.handle_string_field(value, environment)
            elif isinstance(value, dict):
                copy_initial_data[key] = cls.handle_dict_field(value, environment)
            else:
                pass

        created = datetime.datetime.now(tz=pytz.timezone("UTC"))
        last_updated = datetime.datetime.now(tz=pytz.timezone("UTC"))

        if action == 'insert':
            res = (created, last_updated, *copy_initial_data.values())
        elif action == 'update':
            clipped_id = copy_initial_data['id']
            del copy_initial_data['id']
            res = (last_updated, *copy_initial_data.values(), clipped_id)
        else:
            raise ValueError('Could not generate SQL due to invalid action. Its value must be insert or update')
        
        return res
    

    def generate_insert_sql(table: dict) -> str:
        validate_table(table)
        first_data = table['data'][0]
        cols = ["created", "last_updated", *list(first_data.keys())]
        
        insert_vals = "(%s, %s"
        for i in range(len(list(first_data.keys()))):
            insert_vals += ", %s"
        insert_vals += ")"
        insert_sql = f"insert into {table['table-name']} ({', '.join(cols)}) values {insert_vals}"
        return insert_sql

    def generate_update_sql(table: dict) -> str:
        validate_table(table)
        first_data = table['data'][0]
        update_vals = "last_updated = %s"

        for i in range(len(list(first_data.keys()))):
            if list(first_data.keys())[i] != 'id':
                update_vals += ', ' + list(first_data.keys())[i] + " = %s"

        update_sql = f"update {table['table-name']} set {update_vals} where id = %s"
        return update_sql