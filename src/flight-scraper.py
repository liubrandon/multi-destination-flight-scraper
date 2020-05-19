import requests
import json
import gspread
import pygsheets
import time
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint
# Constants
DEPARTURE_HUBS = ("ATL", "ORD", "DFW", "DEN", "LAX", "MIA", "NYCA")
YEAR = "2020"        # MM-DD          MM-DD
DATE_RANGES = ((YEAR+"-05-18", YEAR+"-06-19"),
               (YEAR+"-05-22", YEAR+"-07-31"),
               (YEAR+"-06-05", YEAR+"-07-10"))
SHEET_TITLE = "CIPE Budget Standards Generator"
IATA_CODE_COL = 4

# Google Sheets integration
client = pygsheets.authorize(service_file='/Users/brandonliu/Documents/Documents1/GitHub/multi-destination-flight-scraper/client_secret.json')
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
    if response.status_code != requests.codes.ok:
        print("Skyscanner api call failed")
    # response.raise_for_status()
    jsonData = json.loads(response.text)
    if jsonData == None:
        return -1
    try:
        quotes = jsonData["Quotes"]
    except KeyError:
        return -1
    pricesSum = 0
    for quote in quotes:
        pricesSum += quote["MinPrice"]
    return pricesSum/len(quotes) if len(quotes) != 0 else -1

def initAirportCodesFromColumn(col):
    """Takes a column of city names from col and initializes the column to the right with their corresponding IATA airport code

    Arguments:
        col {int} -- Column # (A->1, B->2,...)
    """
    airportCities = worksheet1.get_col(col, include_tailing_empty=False)
    airportCodes = []
    worksheet1.unlink()
    for i, city in enumerate(airportCities[1:]):
        airportCodes.append(getAirportCode(city)) # can do away with the list here
        time.sleep(1)
        worksheet1.update_value((i+2, 4), airportCodes[i])
    worksheet1.link()

def initHubColumnHeaders():
    col = IATA_CODE_COL + 1
    worksheet1.unlink()
    for hub in DEPARTURE_HUBS:
        worksheet1.update_value((1, col), hub + " Range 1")
        worksheet1.update_value((1, col+1), hub + " Range 2")
        worksheet1.update_value((1, col+2), hub + " Range 3")
        col+=3
    worksheet1.link()

# Object to hold information about a particular destination
class DestinationInfo:
    def __init__(self, row, airportCode):
        self.row = row
        self.airportCode = airportCode

# initAirportCodesFromColumn(IATA_CODE_COL-1)
# initHubColumnHeaders()
airportCodes = worksheet1.get_col(IATA_CODE_COL, include_tailing_empty=False)
#worksheet1.unlink()
startRow = 61
for i, dest in enumerate(airportCodes[startRow-1:]):
    # initialize row and column to the start of the data section
    row = i+startRow
    col = IATA_CODE_COL+1
    for hub in DEPARTURE_HUBS:
        for i, dateRange in enumerate(DATE_RANGES):
            print(f"Getting price for {hub}-{dest} for date range {i+1}")
            avg = getAverageFlightPrice(hub+"-sky", dest+"-sky", dateRange[0], dateRange[1])
            print(f"Average: {avg}")
            time.sleep(1)
            if avg > 0:
                worksheet1.update_value((row, col), avg)
            col+=1
    # After looking up prices for all of the hubs and date ranges,
    # update what time this destination was last checked
    # worksheet1.update_value((row, col), datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
#worksheet1.link()



    

    


