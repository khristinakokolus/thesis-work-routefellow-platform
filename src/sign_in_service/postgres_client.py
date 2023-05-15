from psycopg2 import connect
from datetime import datetime


class PostgresClient:
    def __init__(self, host, port, db_name, password, user):
        self.host = host
        self.port = port
        self.db_name = db_name
        self.password = password
        self.user = user
        self.conn = None
        self.cursor = None

    def connect(self):
        self.conn = connect(
            dbname=self.db_name,
            user=self.user,
            host=self.host,
            password=self.password,
            port=self.port
        )
        self.cursor = self.conn.cursor()
        self.conn.autocommit = True

    def update_record(self,  user_id, field_to_update, data_to_change, table_name):
        current_time = datetime.now()
        query = f"UPDATE {table_name} SET {field_to_update} = '{data_to_change}', updated_at = '{current_time}' WHERE id = '{user_id}';"
        self.cursor.execute(query)

    def select_users(self, table_name):
        query = f"SELECT * from {table_name};"
        self.cursor.execute(query)
        data = self.cursor.fetchall()
        return data

    def select_user_by_email(self, email, table_name):
        query = f"SELECT * from {table_name} WHERE email = '{email}';"
        self.cursor.execute(query)
        data = self.cursor.fetchall()
        return data

    def close_cursor(self):
        self.cursor.close()

    def close_conn(self):
        self.conn.close()