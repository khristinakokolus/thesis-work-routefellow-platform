# User API endpoint
API_PATH = '/search_api'
INSERT_UPDATE_TICKETS = API_PATH + '/insert_update_tickets'

# API vars
KIWI_API_URL = "https://api.tequila.kiwi.com/v2/search"
KIWI_API_KEY = "..."
FLIXBUS_API_URL = "https://flixbus.p.rapidapi.com/v1/search-trips"
FLIXBUS_API_KEY = "...."
FLIXBUS_API_HOST = "flixbus.p.rapidapi.com"

# Path to files
IATA_DATA = "airports.csv"
IATA_DATA_EUROPE = "airports_europe.csv"
AIRLINES_DATA = "airlines.csv"
CITIES_IDS_NAMES = "cities_ids_names.csv"
STATIONS_DATA = "stations.json"


# postgres configs
DB_NAME = "tickets"
USER = "..."
HOST = "..."
PASSWORD = "..."
PORT = "5432"
TRIPS_TABLE_NAME = "trips"
FLIGHTS_TABLE_NAME = "flights"
BUSES_TABLE_NAME = "buses"