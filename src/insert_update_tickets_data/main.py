import variables as var
from get_transport_data import get_flixbus_data, get_kiwi_data
from postgres_client import PostgresClient
import time
import pandas as pd
from utils import extract_unique_iata_codes, extract_unique_city_ids_names, insert_trip_records,\
    insert_flights_records, insert_buses_records, find_min_price_time_ticket,\
    check_flights, check_buses
from datetime import datetime, date, timedelta

postgres_client = PostgresClient(var.HOST, var.PORT, var.DB_NAME, var.PASSWORD, var.USER)
postgres_client.connect()


# run once a day


def delete_redundant_tickets():
    postgres_client.delete_redundant_data(var.TRIPS_TABLE_NAME)
    postgres_client.delete_redundant_data(var.FLIGHTS_TABLE_NAME)
    postgres_client.delete_redundant_data(var.BUSES_TABLE_NAME)


def insert_update_tickets():
    iata_data = pd.read_csv(var.IATA_DATA_EUROPE)
    unique_iata_codes_cities = extract_unique_iata_codes(iata_data)

    cities_ids_names = pd.read_csv(var.CITIES_IDS_NAMES)
    unique_cities_ids_names = extract_unique_city_ids_names(cities_ids_names)

    delta = timedelta(days=1)
    start_date = date.today() + delta
    end_date = date(2023, 8, 30)

    while start_date <= end_date:
        counter = 0

        # insert flights data
        for departure_iata, departure_city in unique_iata_codes_cities.items():
            for arrival_iata, arrival_city in unique_iata_codes_cities.items():
                if departure_iata == arrival_iata:
                    continue

                kiwi_data = get_kiwi_data(departure_iata, arrival_iata, departure_city, arrival_city, start_date)

                counter += 1
                print(counter)
                if counter == 30:
                    time.sleep(60)
                    counter = 0

                if kiwi_data is None or kiwi_data == ([], []):
                    continue
                print(kiwi_data)
                print(len(kiwi_data))
                trips, flights = kiwi_data

                ticket_with_min_price = find_min_price_time_ticket(trips)

                existance = postgres_client.check_existence(ticket_with_min_price[1],
                                                            var.TRIPS_TABLE_NAME)

                if existance[0][0] == True:
                    postgres_client.update_records_trips(ticket_with_min_price, var.TRIPS_TABLE_NAME)
                else:
                    postgres_client.insert_records_trips(ticket_with_min_price, var.TRIPS_TABLE_NAME)
                    filtered = check_flights(flights,ticket_with_min_price[0])

                    for flight in filtered:
                        postgres_client.insert_records_flights(flight, var.FLIGHTS_TABLE_NAME)
        print('got flights data')
        # insert buses data
        for departure_id, departure_point in unique_cities_ids_names.items():
            for arrival_id, arrival_point in unique_cities_ids_names.items():
                if departure_id == arrival_id:
                    continue

                flixbus_data = get_flixbus_data(departure_id, departure_point, arrival_id, arrival_point, '1',
                                                start_date)
                if flixbus_data is None or flixbus_data == ([], []):
                    continue
                trips, buses = flixbus_data

                ticket_with_min_price = find_min_price_time_ticket(trips)

                existance = postgres_client.check_existence(ticket_with_min_price[1],
                                                            var.TRIPS_TABLE_NAME)

                if existance[0][0] == True:
                    postgres_client.update_records_trips(ticket_with_min_price, var.TRIPS_TABLE_NAME)
                else:
                    postgres_client.insert_records_trips(ticket_with_min_price, var.TRIPS_TABLE_NAME)
                    filtered = check_buses(buses, ticket_with_min_price[0])

                    for bus in filtered:
                        postgres_client.insert_records_flights(bus, var.BUSES_TABLE_NAME)
        print("got buses data")

        start_date += delta


if __name__ == '__main__':
    print("started deleting tickets")
    delete_redundant_tickets()
    print("started inserting updates")
    insert_update_tickets()
