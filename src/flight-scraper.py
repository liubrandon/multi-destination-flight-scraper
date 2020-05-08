import requests
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint
# Constants
DEPARTURE_HUBS = ["ATL", "ORD", "DFW", "DEN", "LAX", "MIA", "NYC"]
CURRENCY = "USD"
COUNTRY = "US"
LOCALE = "en-US"

# Google Sheets integration
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("client_secret.json", scope)
client = gspread.authorize(creds)
sheet = client.open("CIPE Budget Standards Generator").sheet1
data = sheet.get_all_records()


def getAirportCode(airportCity):
    "Uses the AirportsFinder API to take the name of an airport (String) and return the first airport code (String)"
    url = "https://cometari-airportsfinder-v1.p.rapidapi.com/api/airports/by-text"
    querystring = {"text": airportCity}
    headers = {
        'x-rapidapi-host': "cometari-airportsfinder-v1.p.rapidapi.com",
        'x-rapidapi-key': "b5ab0a46f1mshd9afbc32fbb45ccp14a1ccjsnd4f777828c87"
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    jsonData = json.loads(response.text)
    return jsonData[0]["code"]


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

# Object to hold information about a particular destination
class DestinationInfo:
    def __init__(self, row, country, airportCity):
        self.row = row
        self.country = country
        self.airportCity = airportCity
        self.airportCode = getAirportCode(airportCity)


testDest = DestinationInfo(1, "Singapore", "Singapore")
print(testDest.airportCode)

# test = getAverageFlightPrice("CHIA-sky", "SINS-sky", "2020-06-15", "2020-08-24")
# print(test)

