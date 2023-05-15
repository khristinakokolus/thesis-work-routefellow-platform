from psycopg2 import connect
from datetime import datetime, date


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

    def insert_records_trips(self, data_to_insert, table_name):
        current_timestamp = datetime.now()
        query = f"INSERT INTO {table_name} (id, api_id, transport_type, type, availability, departure_point, arrival_point, price, duration, departure_time, arrival_time, created_at, updated_at) " \
                f"VALUES ('{data_to_insert[0]}', '{data_to_insert[1]}', '{data_to_insert[2]}'," \
                f" '{data_to_insert[3]}', '{data_to_insert[4]}', '{data_to_insert[5]}', '{data_to_insert[6]}', '{data_to_insert[7]}', '{data_to_insert[8]}', '{data_to_insert[9]}', '{data_to_insert[10]}', '{current_timestamp}', '{current_timestamp}');"
        self.cursor.execute(query)

    def insert_records_flights(self, data_to_insert, table_name):
        current_timestamp = datetime.now()
        query = f"INSERT INTO {table_name} (id, company_name, departure_point, arrival_point, trip_id ,departure_time, arrival_time, created_at, updated_at) " \
                f"VALUES ('{data_to_insert[0]}', '{data_to_insert[1]}', '{data_to_insert[2]}'," \
                f" '{data_to_insert[3]}', '{data_to_insert[4]}', '{data_to_insert[5]}', '{data_to_insert[6]}', '{current_timestamp}', '{current_timestamp}');"
        self.cursor.execute(query)

    def insert_records_buses(self, data_to_insert, table_name):
        current_timestamp = datetime.now()
        query = f"INSERT INTO {table_name} (id, company_name, departure_point, arrival_point, trip_id, departure_time, arrival_time, created_at, updated_at) " \
                f"VALUES ('{data_to_insert[0]}', '{data_to_insert[1]}', '{data_to_insert[2]}'," \
                f" '{data_to_insert[3]}', '{data_to_insert[4]}', '{data_to_insert[5]}', '{data_to_insert[6]}', '{current_timestamp}', '{current_timestamp}');"
        self.cursor.execute(query)

    def check_id_existence(self, id_name, id_value, table_name):
        query = f"SELECT * FROM {table_name} WHERE {id_name} = '{id_value}'"
        self.cursor.execute(query)
        data = self.cursor.fetchall()  # returns list of tuples
        return data

    def update_records_trips(self, data_to_insert, table_name):
        current_timestamp = datetime.now()
        query = f"UPDATE {table_name} SET availability = '{data_to_insert[4]}', price = '{data_to_insert[7]}', duration = '{data_to_insert[8]}', updated_at = '{current_timestamp}' WHERE api_id = '{data_to_insert[1]}';"
        self.cursor.execute(query)

    def check_existence(self, api_id, table_name):
        query = f"select exists(select * from {table_name} WHERE api_id = '{api_id}');"
        self.cursor.execute(query)
        data = self.cursor.fetchall()  # returns list of tuples
        return data

    def delete_redundant_data(self, table_name):
        today = date.today()
        date_year = str(today.year)
        date_month = str(today.month) if len(str(today.month)) != 1 else "0" + str(today.month)
        date_day = str(today.day) if len(str(today.day)) != 1 else "0" + str(today.day)
        date_str = f"{date_year}-{date_month}-{date_day}"
        query = f"DELETE FROM {table_name} WHERE DATE(departure_time) < '{date_str}'"
        self.cursor.execute(query)

    def close_cursor(self):
        self.cursor.close()

    def close_conn(self):
        self.conn.close()
