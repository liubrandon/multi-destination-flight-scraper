import requests
import json
import gspread
import pygsheets
import time
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint
# Constants
DEPARTURE_HUBS = ("ATL", "ORD", "DFW", "DEN", "LAX", "MIA", "NYC")
YEAR = "2021"        # MM-DD          MM-DD
DATE_RANGES = ((YEAR+"-05-15", YEAR+"-06-19"),
               (YEAR+"-05-22", YEAR+"-07-31"),
               (YEAR+"-06-05", YEAR+"-07-10"))
SHEET_TITLE = "CIPE Budget Standards Generator"

# Google Sheets integration
client = pygsheets.authorize(service_file='./client_secret.json')
sheet = client.open(SHEET_TITLE)
worksheet1 = sheet.sheet1

# Skyscanner API Parameters
CURRENCY = "USD"
COUNTRY = "US"
LOCALE = "en-US"

def getAirportCode(airportCity):
    """Uses the AirportsFinder API to take the name of an airport (String) and returns the first airport code (String)
    If no results from the search then returns the empty string"""
    url = "https://cometari-airportsfinder-v1.p.rapidapi.com/api/airports/by-text"
    querystring = {"text": airportCity}
    headers = {
        'x-rapidapi-host': "cometari-airportsfinder-v1.p.rapidapi.com",
        'x-rapidapi-key': "b5ab0a46f1mshd9afbc32fbb45ccp14a1ccjsnd4f777828c87"
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    jsonData = json.loads(response.text)
    return jsonData[0]["code"] if jsonData else ""

def getAverageFlightPrice(originPlace, destinationPlace, outboundPartialDate, inboundPartialDate):
    """Calls Skyscanner Browse Routes Inbound API endpoint and returns the mean price from quotes in their cache

    Arguments:
        originPlace {String} -- Skyscanner place, typically IATA airport code + "-sky"
        destinationPlace {String} -- Same as above
        outboundPartialDate {String} -- "YYYY-MM-DD", "YYYY-MM", or "anytime"
        inboundPartialDate {String} -- Same as above

    Returns:
        Double -- the mean price from quotes in Skyscanner cache
    """
    url = "https://skyscanner-skyscanner-flight-search-v1.p.rapidapi.com/apiservices/browseroutes/v1.0/"+COUNTRY+"/"+CURRENCY+"/"+LOCALE+"/"+originPlace+"/"+destinationPlace+"/"+outboundPartialDate+"/"+inboundPartialDate
    headers = {
        "x-rapidapi-host": "skyscanner-skyscanner-flight-search-v1.p.rapidapi.com",
        "x-rapidapi-key": "b5ab0a46f1mshd9afbc32fbb45ccp14a1ccjsnd4f777828c87"
    }
    response = requests.request("GET", url, headers=headers)
    jsonData = json.loads(response.text)
    quotes = jsonData["Quotes"]
    pricesSum = 0
    for quote in quotes:
        pricesSum += quote["MinPrice"]
    avgPrice = pricesSum/len(quotes)
    return avgPrice


def initAirportCodesFromColumn(col):
    """Takes a column of city names from col and initializes the column to the right with their corresponding IATA airport code

    Arguments:
        col {int} -- Column # (A->1, B->2,...)
    """
    airportCities = worksheet1.get_col(col)
    airportCodes = []
    for i, city in enumerate(airportCities[1:]):
        airportCodes.append(getAirportCode(city))
        time.sleep(1)
        worksheet1.update_value((i+2, 4), airportCodes[i])

# Object to hold information about a particular destination
class DestinationInfo:
    def __init__(self, row, country, airportCity):
        self.row = row
        self.country = country
        self.airportCity = airportCity
        self.airportCode = getAirportCode(airportCity)

# getAirportCodesFromColumn(3)

