from psycopg2 import connect
from datetime import datetime
import pandas as pd

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

    def check_existence(self, api_id, table_name):
        query = f"select exists(select * from {table_name} WHERE api_id = '{api_id}');"
        self.cursor.execute(query)
        data = self.cursor.fetchall()  # returns list of tuples
        return data

    def insert_records_trips(self, data_to_insert, table_name):
        current_timestamp = datetime.now()
        query = f"INSERT INTO {table_name} (id, api_id, transport_type, type, availability, departure_point, arrival_point, price, duration, departure_time, arrival_time, created_at, updated_at) " \
                f"VALUES ('{data_to_insert[0]}', '{data_to_insert[1]}', '{data_to_insert[2]}'," \
                f" '{data_to_insert[3]}', '{data_to_insert[4]}', '{data_to_insert[5]}', '{data_to_insert[6]}', '{data_to_insert[7]}', '{data_to_insert[8]}', '{data_to_insert[9]}', '{data_to_insert[10]}', '{current_timestamp}', '{current_timestamp}');"
        self.cursor.execute(query)

    def insert_records_city_codes(self, data_to_insert, table_name):
        current_timestamp = datetime.now()
        query = f" INSERT INTO {table_name} (city_name, city_code, created_at, updated_at) " \
                f"VAlUES ('{data_to_insert[0]}', '{data_to_insert[1]}', '{current_timestamp}', '{current_timestamp}');"
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

    def update_records_trips(self, data_to_insert, table_name):
        current_timestamp = datetime.now()
        query = f"UPDATE {table_name} SET availability = '{data_to_insert[4]}', price = '{data_to_insert[7]}', duration = '{data_to_insert[8]}', updated_at = '{current_timestamp}' WHERE api_id = '{data_to_insert[1]}';"
        self.cursor.execute(query)

    def select_ticket_by_departure_and_arrival_and_date(self, departure_point, arrival_point, date, table_name,
                                                        transport_type, stopover_during_transportation, adult_number):
        start_date_year = str(date.year)
        start_date_month = str(date.month) if len(str(date.month)) != 1 else "0" + str(date.month)
        start_date_day = str(date.day) if len(str(date.day)) != 1 else "0" + str(date.day)
        date = f"{start_date_year}-{start_date_month}-{start_date_day}"
        query = f"SELECT id, api_id, transport_type, type, availability, departure_point, arrival_point, price, duration, departure_time, arrival_time FROM {table_name} " \
                f"WHERE departure_point = '{departure_point}' " \
                f"AND arrival_point = '{arrival_point}' " \
                f"AND DATE(departure_time) = '{date}' AND availability >= {adult_number} "

        if transport_type == 'flight' or transport_type == 'bus':
            query += f"AND transport_type = '{transport_type}' "

        if stopover_during_transportation == 0:
            query += "AND type in ('Direct', 'Regional', 'Fast', 'Direct Express')"

        query += ';'
        self.cursor.execute(query)
        data = self.cursor.fetchall() # returns list of tuples
        return data

    def select_city_code(self, city_name, table_name):
        query = f"SELECT city_code FROM {table_name} WHERE city_name = '{city_name}'"
        self.cursor.execute(query)
        data = self.cursor.fetchall()  # returns list of tuples
        return data

    def select_optimal_paths_results_both(self, result_api_ids):
        query = f"""WITH trips_info AS (
                    SELECT 
                        id,
                        api_id,
                        transport_type,
                        type,
                        availability,
                        departure_point AS departure_point_trips,
                        arrival_point AS arrival_point_trips,
                        price,
                        duration
                    FROM trips
                    WHERE api_id 
                    IN {tuple(result_api_ids)}
                ),
                
                flights_info AS (
                    SELECT
                        company_name,
                        departure_point,
                        arrival_point,
                        trip_id,
                        arrival_time,
                        departure_time
                    FROM flights
                ),
                
                buses_info AS (
                    SELECT
                    company_name,
                        departure_point,
                        arrival_point,
                        trip_id,
                        arrival_time,
                        departure_time
                    FROM buses
                ),
                result AS (
                    SELECT *
                    FROM trips_info
                    INNER JOIN flights_info on trips_info.id = flights_info.trip_id
                    WHERE trips_info.transport_type = 'flight'
                    
                    UNION
                    
                    SELECT *
                    FROM trips_info
                    INNER JOIN buses_info on trips_info.id = buses_info.trip_id
                    WHERE trips_info.transport_type = 'bus'
                )
                SELECT *
                FROM result
                ORDER BY departure_time
                """
        df = pd.read_sql(query, con=self.conn)
        return df

    def close_cursor(self):
        self.cursor.close()

    def close_conn(self):
        self.conn.close()
