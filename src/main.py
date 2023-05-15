from flask import Flask, render_template, request, redirect, url_for, session
import requests
import json
import variables as var
from utils import format_output_main, format_output_detailed,check_entered_fields


app = Flask(__name__)
app.secret_key = "super secret key"

EMAIL_LOGGED_IN_USERS = []


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/sign_up", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        data = {"username": username, "email": email, "password": password}
        response = requests.post(url=var.SIGN_UP_SERVICE_URL, data=json.dumps(data),
                                headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            return redirect(url_for('sign_in'))
        else:
            return render_template('error.html', error=response.json()['results'])
    return render_template("sign_up.html")


@app.route("/sign_in", methods=["GET", "POST"])
def sign_in():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        data = {"email": email, "password": password}
        EMAIL_LOGGED_IN_USERS.append(email)
        print(data)
        response = requests.post(url=var.SIGN_IN_SERVICE_URL, data=json.dumps(data),
                                 headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            session['email'] = email

            requests.post(url=var.SIGN_OUT_SERVICE_URL, data=json.dumps(data),
                          headers={"Content-Type": "application/json"})
            return redirect(url_for('search'))
        elif response.json()['results'] == 'ERROR, you need to sign up first':
            return redirect(url_for('sign_up'))
        else:
            print(response)
            print(response.status_code)
            return render_template('error.html', error=response.json()['results'])
    return render_template("sign_in.html")


@app.route("/sign_out", methods=["GET", "POST"])
def sign_out():
    # if session['email'] in EMAIL_LOGGED_IN_USERS:
    #     data = {"email": session['email']}
    #     response = requests.post(url=var.SIGN_OUT_SERVICE_URL, data=json.dumps(data),
    #                              headers={"Content-Type": "application/json"})
    #     EMAIL_LOGGED_IN_USERS.remove(session['email'])
    #     if response.status_code == 200:
    #         return redirect(url_for('home'))
    return redirect(url_for('home'))


@app.route("/search", methods=["GET", 'POST'])
def search():
    if request.method == "POST":
        departure_destination = request.form.get("departure_destination").replace(" ", "")
        other_destinations = request.form.get("other_destinations").replace(" ", "")
        days_in_cities = request.form.get("days_in_cities").replace(" ", "")
        date_from = request.form.get("date_from").replace(" ", "")
        date_to = request.form.get("date_to").replace(" ", "")
        price_max = request.form.get("price_max").replace(" ", "")
        stopover_during_transportation = request.form.get("stopover_during_transportation").replace(" ", "")
        adult_number = request.form.get("adult_number").replace(" ", "")
        search_buses_flights = request.form.get("search_buses_flights").replace(" ", "")
        airlines_to_exclude = request.form.get("airlines_to_exclude")

        error, error_msg = check_entered_fields(other_destinations, days_in_cities, date_from, date_to, search_buses_flights)

        if error:
            return render_template('error.html', error=error_msg)

        data = {"departure_destination": departure_destination, "other_destinations": other_destinations,
                "days_in_cities": days_in_cities, "date_from": date_from, "date_to": date_to,
                "price_max": price_max, "stopover_during_transportation": stopover_during_transportation,
                "adult_number": adult_number, "search_buses_flights": search_buses_flights,
                "airlines_to_exclude": airlines_to_exclude
        }

        response = requests.post(url=var.SEARCH_SERVICE_URL, data=json.dumps(data),
                                 headers={"Content-Type": "application/json"})

        if response.status_code == 200:
            json_data = json.loads(response.json()['results'])

            cities_dct, paths, results_data = json_data

            if len(paths) == 0:
                return render_template('error.html', error='No paths with such search parameter. Please, check and try again with other ones.')

            headers_main_table = ['Num', 'Cities order', 'Total price (EUR)', 'Total transportation time (Hours)']

            tableData_main = format_output_main(cities_dct, paths)

            header_detailed_tables = ['Path', 'Price (EUR)', 'Transportation time (Hours)', 'Carrier', 'Local departure time',
                                      'Local arrival time']

            table_data_detailed = format_output_detailed(cities_dct, paths, tableData_main, results_data)

            return render_template(
                'results.html',
                headers_main_table=headers_main_table,
                tableData_main=tableData_main,
                header_detailed_tables=header_detailed_tables,
                tableData=table_data_detailed
            )
        else:
            return render_template('error.html', error='ERROR happened, please, go back to Search, check query params and try again.')
    return render_template("search.html")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5004')
