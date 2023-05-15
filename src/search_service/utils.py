import pandas as pd
import variables as var
from datetime import datetime, timedelta
from itertools import permutations


def make_days_in_cities_combinations(days_ranges):
    combs = list(permutations(days_ranges))
    return combs


def generate_travel_dates(date_from, date_to, days_combinations):
    date_from_datetime = datetime.strptime(date_from, '%d.%m.%Y').date()
    date_to_datetime = datetime.strptime(date_to, '%d.%m.%Y').date()

    initial_date_from = datetime.strptime(date_from, '%d.%m.%Y').date()

    poss_dates = [date_from_datetime]
    for days in days_combinations:
        date_from_datetime = initial_date_from
        for day in days:
            date_from_datetime += timedelta(days=int(day))
            poss_dates.append(date_from_datetime)

    print(poss_dates)
    poss_dates_without_dups = list(set(poss_dates))
    print(poss_dates_without_dups)
    poss_dates_without_dups.sort()
    poss_dates_without_dups_str = [value.strftime('%d.%m.%Y') for value in poss_dates_without_dups]

    return poss_dates_without_dups_str[1:-1]


def get_airline_name(airline_code):
    airline_data = pd.read_csv(var.AIRLINES_DATA)
    airline_name = airline_data[airline_data["IATA"] == airline_code]

    if len(airline_name["Name"].tolist()) == 0:
        return airline_code
    return airline_name["Name"].tolist()[0]


def get_airline_codes(airline_names):
    airline_codes = []
    for airline_name in airline_names:
        airline_data = pd.read_csv(var.AIRLINES_DATA)
        airline_code = airline_data[airline_data["Name"] == airline_name]

        if len(airline_code["IATA"].tolist()) == 0:
            continue
        airline_codes.append(airline_code["IATA"].tolist()[0])
    return ','.join(airline_codes)


def construct_lst_for_tsp_problem(data_matrix, indx):
    lst = []
    for city in data_matrix:
        tmp_list = []
        for value in city:
            if value == [0]:
                tmp_list.append([0])
            elif len(value) > 1 and len(value) != 11: # do not select created at and updated at
                tmp_lst_tickets = []
                for ticket in value:
                    if ticket == []:
                        tmp_lst_tickets.append(())
                    else:
                        tmp_lst_tickets.append(ticket[indx])
                tmp_list.append(tmp_lst_tickets)
            elif value == []:
                tmp_list.append(())
            else:
                tmp_list.append([value[indx]])
        lst.append(tmp_list)
    return lst


def find_min_price_time_ticket(possible_tickets):
    return list(min(possible_tickets, key=lambda x: x[7] + x[8]))


def check_flights(flights, buses, id):
    filtered = []

    for value in flights:
        if id in value:
            filtered.append(value)
    if filtered:
        return ('flight', filtered)

    for value in buses:
        if id in value:
            filtered.append(value)
    return ('bus', filtered)

