from flask import Flask, request, make_response, jsonify
import numpy as np
import variables as var
from get_transport_data import get_city_code, find_tickets
from postgres_client import PostgresClient
from utils import make_days_in_cities_combinations, generate_travel_dates, construct_lst_for_tsp_problem
from datetime import datetime, timedelta
from tsp_solver import make_possible_combinations, filter_combinations, make_possible_tsp_tasks, solve_tsp
import json
from threading import Thread

app = Flask(__name__)

postgres_client = PostgresClient(var.HOST, var.PORT, var.DB_NAME, var.PASSWORD, var.USER)
postgres_client.connect()


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)



@app.route('/', methods=['GET'])
def sign_up_get():
    return "Welcome to search service"

@app.route(var.SEARCH, methods=['POST'])
def search():
    departure_destination = request.json['departure_destination']
    other_destinations = request.json['other_destinations'].split(",")
    days_in_cities = request.json['days_in_cities'].split(",")
    date_from = request.json['date_from']
    date_to = request.json['date_to']
    max_total_price = int(request.json['price_max'])
    stopover_during_transportation = int(request.json['stopover_during_transportation'])
    adult_number = int(request.json['adult_number'])
    search_buses_flights = request.json['search_buses_flights']
    airlines_to_exclude = request.json['airlines_to_exclude'].split(",")

    destinations_together = [departure_destination] + other_destinations  # departure point plus other destinations

    # save somewhere globally this name
    city_codes_dct = dict()  # dictionary with codes of the city for flights search
    for city in destinations_together:
        city_code = postgres_client.select_city_code(city, var.CITY_CODES_TABLE)
        if city_code:
            city_codes_dct[city] = city_code[0][0]
        else:
            city_code = get_city_code(city)
            city_codes_dct[city] = city_code
            postgres_client.insert_records_city_codes([city, city_code], var.CITY_CODES_TABLE)

    # combinations of possible dates to travel
    dates_combinations_to_travel = make_days_in_cities_combinations(days_in_cities)
    print(dates_combinations_to_travel)
    possible_travel_dates = generate_travel_dates(date_from, date_to, dates_combinations_to_travel)

    print(possible_travel_dates)

    cities_amount = len(other_destinations) + 1
    destinations_with_days_in = dict(zip(other_destinations, days_in_cities))
    print(destinations_with_days_in)

    cities_values = np.array(list(range(1, cities_amount)))
    destinations_with_days_in_tsp = dict(zip(cities_values, days_in_cities))

    # Find all tickets from departure points to other ones
    from_dest_tickets = [[0]]
    date_from_datetime = datetime.strptime(date_from, '%d.%m.%Y').date()
    for arrival in other_destinations:

        ticket = find_tickets(postgres_client, date_from_datetime,
                              departure_destination, arrival, search_buses_flights,
                              city_codes_dct, adult_number, airlines_to_exclude,
                              stopover_during_transportation)

        from_dest_tickets.append(ticket)

    # Find all possible tickets between locations

    tickets_between_diff_destinations = []
    for departure in other_destinations:
        tickets_departure_arrival = []
        for arrival in other_destinations:
            if departure == arrival:
                continue
            travel_dates_tickets = []
            for travel_date in possible_travel_dates:
                travel_date_datetime = datetime.strptime(travel_date, '%d.%m.%Y').date()
                if travel_date_datetime + timedelta(days=int(destinations_with_days_in[departure])) > datetime.strptime(date_to, '%d.%m.%Y').date():
                    continue

                ticket = find_tickets(postgres_client, travel_date_datetime,
                                      departure, arrival, search_buses_flights,
                                      city_codes_dct, adult_number,
                                      airlines_to_exclude, stopover_during_transportation )

                travel_dates_tickets.append(ticket)

            if len(travel_dates_tickets) == 1:
                tickets_departure_arrival = travel_dates_tickets
            else:
                tickets_departure_arrival.append(travel_dates_tickets)
        tickets_between_diff_destinations.append(tickets_departure_arrival)

    # Find all tickets back to departure points
    back_to_dest_tickets = []
    date_to_datetime = datetime.strptime(date_to, '%d.%m.%Y').date()
    for departure_back in other_destinations:

        ticket = find_tickets(postgres_client, date_to_datetime, departure_back, departure_destination,
                 search_buses_flights, city_codes_dct, adult_number,
                 airlines_to_exclude, stopover_during_transportation)
        back_to_dest_tickets.append(ticket)

    # add back tickets to the list where are data about all the destinations with zeros
    tickets_diff_dest_with_back = []
    i = 0
    for value in tickets_between_diff_destinations:
        value.insert(0, back_to_dest_tickets[i])
        value.insert(i+1, [0])
        i += 1
        tickets_diff_dest_with_back.append(value)

    # construct matrix for tsp problem - first only with prices to see data look
    data_matrix = []
    data_matrix.append(from_dest_tickets)
    data_matrix.extend(tickets_diff_dest_with_back)

    print("Data Matrix: ", data_matrix)

    # construct_prices_lst
    prices_on_diff_dates = construct_lst_for_tsp_problem(data_matrix, 7)
    travel_times_on_diff_dates = construct_lst_for_tsp_problem(data_matrix, 8)
    travel_dates_data = construct_lst_for_tsp_problem(data_matrix, 9)
    ticket_ids = construct_lst_for_tsp_problem(data_matrix, 1)

    combinations_prices, \
    combinations_travel_times, \
    combinations_travel_dates, \
    combinations_tickets = make_possible_combinations(cities_amount, days_in_cities, prices_on_diff_dates,
                            travel_times_on_diff_dates, travel_dates_data, ticket_ids)

    filtered_combinations_prices, filtered_combinations_travel_times,\
    filtered_combinations_travel_dates, filtered_combinations_tickets = filter_combinations(combinations_travel_dates,
                                                                                            combinations_prices,
                        combinations_travel_times, combinations_tickets)

    prices, travel_times, \
    travel_dates, tickets_ids = make_possible_tsp_tasks(filtered_combinations_prices, filtered_combinations_travel_times,
                                                        filtered_combinations_travel_dates, filtered_combinations_tickets)

    problems_amount = len(prices)
    print("Problems amount: ", problems_amount)
    possible_tickets = np.array(list(range(cities_amount)))
    indexes = list(range(cities_amount))
    cities_dct = dict(zip(indexes, destinations_together))

    results_dict = solve_tsp(problems_amount, possible_tickets, prices, travel_times, travel_dates,
                             tickets_ids, cities_amount, max_total_price, cities_amount,
                             destinations_with_days_in_tsp)

    results_sorted = sorted(results_dict.items(), key=lambda x: x[1][1])
    converted_dict = dict(results_sorted)
    paths = []
    for result in converted_dict.values():
        if result not in paths:
            paths.append(result)

    if len(paths) > 10:
        paths = paths[:10]

    results_data = []
    for path in paths:
        result = postgres_client.select_optimal_paths_results_both(path[2])
        results_data.append(result.to_json())

    total_data = [cities_dct, paths, results_data]

    return make_response(jsonify(
        results=json.dumps(total_data, cls=NpEncoder)
    ), 200)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5003')
