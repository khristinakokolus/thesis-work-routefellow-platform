import pandas as pd
from datetime import datetime


def check_entered_fields(other_destinations, days_in_cities, date_from, date_to, search_buses_flights):
    if search_buses_flights != 'flight' and search_buses_flights != 'bus' and search_buses_flights != 'both':
        return (True,'Incorrect \'Transport options you want travel with\' field, possible values ONLY: flight, bus or both. Please, check fields and try again')

    elif len(other_destinations.split(',')) != len(days_in_cities.split(',')):
        return (True, 'Please, enter amount of days you want to spend in ALL cities seperately. Please, check and try again.')

    date_from_datetime = datetime.strptime(date_from, '%d.%m.%Y').date()
    date_day_from = int(str(date_from_datetime.day))

    date_to_datetime = datetime.strptime(date_to, '%d.%m.%Y').date()
    date_day_to = int(str(date_to_datetime.day))

    days_lst = days_in_cities.split(',')

    for day in days_lst:
        date_day_from += int(day)

    if date_day_from != date_day_to:
        return ( True, 'Please, check dates of jouney together with days to spend in destinations. Date of arrival is incorrect, please try again.')

    return (False, 'no errors')


def create_cities_order(cities_dct, path):
    cities_order = ''
    for value in path:
        cities_order += cities_dct[str(value)] + '-'
    cities_order += cities_dct['0']
    return cities_order


def format_output_main(cities_dct, paths):
    table_data_main = []
    results_amount = len(paths)

    for i in range(results_amount):
        temp_dict = dict()
        temp_dict['Num'] = i + 1
        temp_dict['Cities order'] = create_cities_order(cities_dct, paths[i][0])
        temp_dict['Total price'] = paths[i][3]
        temp_dict['Total transportation time'] = paths[i][4]
        table_data_main.append(temp_dict)
    return table_data_main


def format_output_detailed(cities_dct, paths, table_data_main, results_data):
    table_data_detailed = []
    results_amount = len(paths)

    for i in range(results_amount):
        temp_lst = []
        for k in range(len(paths[i][0])):
            temp_dict = dict()
            if k == len(paths[i][0]) - 1:
                temp_dict['Path'] = cities_dct[str(paths[i][0][k])] + '-' + cities_dct[str(paths[i][0][0])]
            else:
                temp_dict['Path'] = cities_dct[str(paths[i][0][k])] + '-' + cities_dct[str(paths[i][0][k + 1])]
            df = pd.read_json(results_data[i])
            print(len(df.index))
            print(df)
            certain_api_id_data = df[df['api_id'] == paths[i][2][k]]
            print(paths[i][2][k])
            if len(certain_api_id_data.index) > 1:
                temp_dict['Path'] = '-'.join(certain_api_id_data['departure_point'].to_list() + [certain_api_id_data['arrival_point'].to_list()[-1]])
                print(temp_dict['Path'])
            temp_dict['Price'] = certain_api_id_data['price'].to_list()[0]
            temp_dict['Transportation time'] = certain_api_id_data['duration'].to_list()[0]
            temp_dict['Carrier'] = ', '.join(certain_api_id_data['company_name'].to_list())
            temp_dict['Local departure time'] = ', '.join(map(str,certain_api_id_data['departure_time'].to_list()))
            temp_dict['Local arrival time'] = ', '.join(map(str,certain_api_id_data['arrival_time'].to_list()))

            temp_lst.append(temp_dict)
        temp_lst[0]['Optimal path'] = table_data_main[i]['Cities order']
        table_data_detailed.append(temp_lst)

    return table_data_detailed


