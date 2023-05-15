import pandas as pd
import variables as var


def insert_trip_records(postgres_client, data):
    for value in data:
        postgres_client.insert_records_trips(value, var.TRIPS_TABLE_NAME)


def insert_flights_records(postgres_client, data):
    for value in data:
        postgres_client.insert_records_flights(value, var.FLIGHTS_TABLE_NAME)


def insert_buses_records(postgres_client, data):
    for value in data:
        postgres_client.insert_records_flights(value, var.BUSES_TABLE_NAME)


def find_min_price_time_ticket(possible_tickets):
    print(possible_tickets)
    return list(min(possible_tickets, key=lambda x: x[7] + x[8]))


def check_flights(flights, id):
    filtered = []

    for value in flights:
        if id in value:
            filtered.append(value)
    return filtered


def check_buses(buses, id):
    filtered = []

    for value in buses:
        if id in value:
            filtered.append(value)
    return filtered


def extract_unique_city_ids_names(city_ids_names):
    dataset_length = len(city_ids_names.index)
    city_ids = city_ids_names['city_id']
    city_names = city_ids_names['city_name']

    unique_ids_names = dict()

    for i in range(dataset_length):
        if city_ids[i] not in unique_ids_names.keys():
            unique_ids_names[str(city_ids[i])] = city_names[i]

    return unique_ids_names


def extract_unique_iata_codes(iata_data):
    dataset_length = len(iata_data.index)
    iata_codes = iata_data['IATA']
    iata_cities = iata_data['City']

    iata_data_dct = dict()

    for i in range(dataset_length):
        if iata_codes[i] == "\\N":
            continue
        iata_data_dct[iata_codes[i]] = iata_cities[i]

    return iata_data_dct


def extract_airport_iata_code(city_name):
    iata_code_data = pd.read_csv(var.IATA_DATA)
    iata_code_city = iata_code_data[iata_code_data["City"] == city_name]

    return iata_code_city["IATA"].tolist()


def get_airline_name(airline_code):
    airline_data = pd.read_csv(var.AIRLINES_DATA)
    airline_name = airline_data[airline_data["IATA"] == airline_code]

    if len(airline_name["Name"].tolist()) == 0:
        return airline_code
    return airline_name["Name"].tolist()[0]
