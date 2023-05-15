import json
import requests
from utils import get_airline_name, get_airline_codes, find_min_price_time_ticket, check_flights
import variables as var
import uuid
import pandas as pd
from datetime import datetime
import time


def get_flixbus_data(departure_destination, arrival_destination, adult_number, date, stopover_during_transportation):

    try:
        f = open(var.STATIONS_DATA)
        stations_data = json.load(f)
        f.close()

        city_ids_names_data = pd.read_csv(var.CITIES_IDS_NAMES)
        flixbus_date = convert_to_flixbus_date(date)

        departure_id = city_ids_names_data[city_ids_names_data['city_name'] == departure_destination]["city_id"].values[0]
        arrival_id = city_ids_names_data[city_ids_names_data['city_name'] == arrival_destination]["city_id"].values[0]

        query = {"to_id": arrival_id, "from_id": departure_id, "currency": "EUR", "departure_date": flixbus_date,
                       "number_adult": adult_number, "search_by": "cities"}

        headers = {
            "X-RapidAPI-Key": var.FLIXBUS_API_KEY,
            "X-RapidAPI-Host": var.FLIXBUS_API_HOST
        }

        response = requests.request("GET", var.FLIXBUS_API_URL, headers=headers, params=query)

        if not response.json():
            return ([], [])
        data = response.json()[0]['items']
        trips = []
        buses = []
        for value in data:
            if value["status"] == "available":
                trip_id = str(uuid.uuid4())
                bus_id = str(uuid.uuid4())

                departure_time = datetime.fromtimestamp(value["departure"]["timestamp"])
                if departure_time.date() != date:
                    continue
                arrival_time = datetime.fromtimestamp(value["arrival"]["timestamp"])

                duration = round(value['duration']['hour'] + value['duration']['minutes'] / 60, 2)


                trip_info = (trip_id, value["uid"], "bus", value['transfer_type'], value['available']['seats'],
                             departure_destination, arrival_destination, value["price_average"],
                             duration, departure_time, arrival_time)

                if value["interconnection_transfers"]:
                    if stopover_during_transportation == 0:
                        continue
                    middle_point_city_name = None
                    middle_point_station = value["interconnection_transfers"][0]["station_id"]

                    for station in stations_data:
                        if station['id'] == middle_point_station:
                            middle_point_city_name = station["city_name"]
                            break
                    if middle_point_city_name is None:
                        continue
                    bus_info1 = (str(uuid.uuid4()), "Flixbus", departure_destination, middle_point_city_name, trip_id,
                                departure_time, datetime.fromtimestamp(value["interconnection_transfers"][0]["arrival"]["timestamp"]))
                    bus_info2 = (str(uuid.uuid4()), "Flixbus", middle_point_city_name, arrival_destination, trip_id,
                                 datetime.fromtimestamp(value["interconnection_transfers"][0]["departure"]["timestamp"]), arrival_time)

                    buses.append(bus_info1)
                    buses.append(bus_info2)
                else:
                    bus_info = (bus_id, "Flixbus", departure_destination, arrival_destination, trip_id,
                               departure_time, arrival_time)
                    buses.append(bus_info)

                trips.append(trip_info)
        trips_and_buses = (trips, buses)
        return trips_and_buses
    except Exception:
        return ([], [])


def get_kiwi_data(departure_code, arrival_code, departure_destination, arrival_destination,
                  adult_number, date, exclude_airlines=None,
                  max_stopovers=None):
    trips = []
    flights = []

    kiwi_date = convert_to_kiwi_date(date)

    query = {"fly_from": 'city:' + departure_code, "fly_to": "city:" + arrival_code,
             "dateFrom": kiwi_date, "dateTo": kiwi_date, "adults": adult_number}
    if exclude_airlines is not None:
        converted_excluded_airlines = get_airline_codes(exclude_airlines)
        query['select_airlines'] = converted_excluded_airlines
        query['select_airlines_exclude'] = "True"
    if max_stopovers is not None:
        query['max_stopovers'] = max_stopovers

    header = {"apikey": var.KIWI_API_KEY}
    response = requests.request("GET", var.KIWI_API_URL, headers=header, params=query)
    response_json = response.json()
    if response_json == {'error_code': 429, 'message': 'Rate limit exceeded'}:
        time.sleep(60)
        response = requests.request("GET", var.KIWI_API_URL, headers=header, params=query)
        response_json = response.json()

    if 'data' not in response_json.keys():
        return ([], [])
    data = response_json['data']
    for value in data:

        if value['availability']['seats'] is not None:

            trip_id = str(uuid.uuid4())

            type = 'Transfer' if len(value['route']) > 1 else 'Direct'
            duration = round(value['duration']['departure'] / 3600, 2)

            # Prices now are only in Euro
            trip_info = (trip_id, value["id"],"flight", type, value['availability']['seats'],
                         departure_destination, arrival_destination, value["fare"]['adults'],
                         duration, value["local_departure"], value["local_arrival"])
            trips.append(trip_info)

            for route in value["route"]:
                airline = route['airline']
                airline_name = get_airline_name(airline)
                flight_id = str(uuid.uuid4())
                flight_info = (flight_id, airline_name, route["cityFrom"], route["cityTo"], trip_id,
                               route["local_departure"], route["local_arrival"])
                flights.append(flight_info)

    trips_and_flights = (trips, flights)
    return trips_and_flights


def find_tickets(postgres_client, date_timestamp, departure, arrival,
                 search_buses_flights, city_codes_dct, adult_number,
                 airlines_to_exclude, stopover_during_transportation):

    possible_tickets = postgres_client.select_ticket_by_departure_and_arrival_and_date(
        departure, arrival, date_timestamp, var.TRIPS_TABLE_NAME, search_buses_flights,
        stopover_during_transportation, adult_number)

    if possible_tickets:
        ticket_with_min_price = find_min_price_time_ticket(possible_tickets)
        return ticket_with_min_price

    else:  # getting data from api

        if search_buses_flights == 'both':
            kiwi_data = get_kiwi_data(city_codes_dct[departure], city_codes_dct[arrival],
                                      departure, arrival, adult_number, date_timestamp,
                                      airlines_to_exclude, stopover_during_transportation)
            bus_data = get_flixbus_data(departure, arrival, str(adult_number), date_timestamp, stopover_during_transportation)
        elif search_buses_flights == 'flight':
            kiwi_data = get_kiwi_data(city_codes_dct[departure], city_codes_dct[arrival],
                                      departure, arrival, adult_number, date_timestamp,
                                      airlines_to_exclude, stopover_during_transportation)
            bus_data = ([], [])
        elif search_buses_flights == 'bus':
            kiwi_data = ([], [])
            bus_data = get_flixbus_data(departure, arrival, str(adult_number), date_timestamp,
                                        stopover_during_transportation)

        # get data about buses also and from both of them get ticket with min price
        if (kiwi_data == ([], [])) and (bus_data == ([], [])):
            return [None, None, None, None, None, None, None,
                    1000, 1000, None, None]
        else:
            trips_flights, flights = kiwi_data
            trips_bus, buses = bus_data
            trips = trips_flights + trips_bus

            ticket_with_min_price = find_min_price_time_ticket(trips)
            existance = postgres_client.check_existence(ticket_with_min_price[1],
                                                        var.TRIPS_TABLE_NAME)
            if existance[0][0] == True:
                postgres_client.update_records_trips(ticket_with_min_price, var.TRIPS_TABLE_NAME)
            else:
                postgres_client.insert_records_trips(ticket_with_min_price, var.TRIPS_TABLE_NAME)
                fl_type, filtered = check_flights(flights, buses, ticket_with_min_price[0])

                if fl_type == 'flight':
                    for flight in filtered:
                        postgres_client.insert_records_flights(flight, var.FLIGHTS_TABLE_NAME)
                else:
                    for bus in filtered:
                        postgres_client.insert_records_flights(bus, var.BUSES_TABLE_NAME)

            return list(postgres_client.select_ticket_by_departure_and_arrival_and_date(
                departure, arrival, date_timestamp, var.TRIPS_TABLE_NAME, search_buses_flights,
                stopover_during_transportation, adult_number)[0])


def get_city_code(city_name):
    query = {'term': city_name, 'locale': 'en-US', 'location_types': 'city', 'limit': 1, 'active_only': True}

    header = {"apikey": var.KIWI_API_KEY}
    response = requests.request("GET", var.KIWI_API_LOCATIONS_URL, headers=header, params=query)

    return response.json()['locations'][0]['code']


def convert_to_kiwi_date(date_datetime):
    date_year = str(date_datetime.year)
    date_month = str(date_datetime.month) if len(str(date_datetime.month)) != 1 else "0" + str(
        date_datetime.month)
    date_day = str(date_datetime.day) if len(str(date_datetime.day)) != 1 else "0" + str(
        date_datetime.day)

    kiwi_date = f"{date_day}/{date_month}/{date_year}"
    return kiwi_date


def convert_to_flixbus_date(date_datetime):
    date_year = str(date_datetime.year)
    date_month = str(date_datetime.month) if len(str(date_datetime.month)) != 1 else "0" + str(
        date_datetime.month)
    date_day = str(date_datetime.day) if len(str(date_datetime.day)) != 1 else "0" + str(
        date_datetime.day)

    flixbus_date = f"{date_year}-{date_month}-{date_day}"
    return flixbus_date