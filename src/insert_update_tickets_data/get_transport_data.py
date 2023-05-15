import json
import requests
from utils import get_airline_name
from datetime import datetime
import variables as var
import uuid
import time


def get_flixbus_data(departure_id, departure_destination, arrival_id, arrival_destination, adult_number, date):
    try:
        f = open(var.STATIONS_DATA)
        stations_data = json.load(f)
        f.close()

        flixbus_date = convert_to_flixbus_date(date)

        query = {"to_id": arrival_id, "from_id": departure_id, "currency": "EUR", "departure_date": flixbus_date,
                 "number_adult": adult_number, "search_by": "cities"}

        headers = {
            "X-RapidAPI-Key": var.FLIXBUS_API_KEY,
            "X-RapidAPI-Host": var.FLIXBUS_API_HOST
        }

        response = requests.request("GET", var.FLIXBUS_API_URL, headers=headers, params=query)
        if not response.json():
            return None

        data = response.json()[0]['items']
        trips = []
        buses = []
        for value in data:
            if value["status"] == "available":
                trip_id = str(uuid.uuid4())
                bus_id = str(uuid.uuid4())

                departure_time = datetime.fromtimestamp(value["departure"]["timestamp"])
                arrival_time = datetime.fromtimestamp(value["arrival"]["timestamp"])

                duration = round(value['duration']['hour'] + value['duration']['minutes'] / 60, 2)

                trip_info = (trip_id, value["uid"], "bus", value['transfer_type'], value['available']['seats'],
                             departure_destination, arrival_destination, value["price_average"],
                             duration, departure_time, arrival_time)
                trips.append(trip_info)

                if value["interconnection_transfers"]:
                    middle_point_station = value["interconnection_transfers"][0]["station_id"]
                    middle_point_city_name = None

                    for station in stations_data:
                        if station['id'] == middle_point_station:
                            middle_point_city_name = station["city_name"]
                            break
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
        trips_and_buses = (trips, buses)
        return trips_and_buses
    except Exception:
        return None


def get_kiwi_data(departure_iata, arrival_iata, departure_destination, arrival_destination, date, exclude_airlines=None,
                  max_stopovers=None):
    trips = []
    flights = []

    kiwi_date = convert_to_kiwi_date(date)

    query = {"fly_from": departure_iata, "fly_to": arrival_iata, "dateFrom": kiwi_date}
    if exclude_airlines is not None:
        query['select_airlines'] = exclude_airlines
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
        return None
    data = response_json['data']
    for value in data:
        if value['availability']['seats'] is not None:

            trip_id = str(uuid.uuid4())

            type = 'Transfer' if len(value['route']) > 1 else 'Direct'
            duration = round(value['duration']['departure'] / 3600, 2)

            # Prices now are only in Euro
            trip_info = (trip_id, value["id"], "flight", type, value['availability']['seats'],
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