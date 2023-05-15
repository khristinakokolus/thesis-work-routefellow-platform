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

    def insert_records(self, data_to_insert, table_name):
        current_timestamp = datetime.now()
        query = f"INSERT INTO {table_name} (id, username, email, password, log_in, created_at, updated_at) " \
                f"VALUES ('{data_to_insert[0]}', '{data_to_insert[1]}', '{data_to_insert[2]}'," \
                f" '{data_to_insert[3]}', '{data_to_insert[4]}', '{current_timestamp}', '{current_timestamp}');"
        self.cursor.execute(query)

    def select_user_by_username_and_email(self, username, email, table_name):
        query = f"SELECT * FROM {table_name} WHERE username = '{username}' AND email = '{email}';"
        self.cursor.execute(query)
        data = self.cursor.fetchall()
        return data

    def close_cursor(self):
        self.cursor.close()

    def close_conn(self):
        self.conn.close()
