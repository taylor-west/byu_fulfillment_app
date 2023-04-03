import json
from datetime import *
from dateutil import tz
import sys
import os
import logging

import requests as req
from .._Reference.bite_info import CONTENT_TYPE, X_MD_API_VERSION, AUTHORIZATION_TOKEN
from .._Reference.bite_info import LOCATIONS_PAGE_VALUE, LOCATIONS_LIMIT_VALUE
from .._Reference.bite_info import REPORTING_PAGE_VALUE, REPORTING_LIMIT_VALUE

########################################################################################################################
#           ABOUT:  This script pulls data from the Bite API about every orderw placed that day for a specified list of
#           locations. It is used in the Campus Pickup Fulfillment App by BYU Dining Services.
#           Authors: Taylor West
#           BITE API documentation can be found here: https://documentation.getbite.com/
########################################################################################################################

BITE_LOCATION_IDS_FILE_URL = "./_Reference/bite_location_ids.json"

def get_order_data(desired_locations: list, 
                   report_date = datetime.now(timezone.utc).astimezone(tz.gettz('Mountain Standard Time'))
                   ) -> dict:
    """
    Calls the Reporting API for each of the locations specified and returns a list of the JSON responses.

    Parameters
    ------------
        desired_locations: list of strings
            The name of each location that you want to generate a report for

        update_location_ids: bool
            Whether you want to use the pre-defined list of constant ID's or query the Locations API. If set to FALSE, will use SANDBOX_LOCATION_IDS as the list of location names to search.

        report_date: str
            The date for which to generate the report. Formatted 'YYYY-MM-DD'. Defaults to the current date.

    Returns
    -----------
        response_list: list
            The JSON responses from Reporting API for each of the locations specified in locations_names_array
        
    Dependencies
    ------------
        calls get_reporting_data()

        ./PullOrdersBiteAPI/reference/bite_location_ids.json
            a JSON file containing a list of Bite sites and the associated channel id's
    """

    # read in the list of order ID's
    with open(BITE_LOCATION_IDS_FILE_URL, "r") as dict_file:
        location_ids = json.load(dict_file)

    # makes sure that we have a valid date
    if isinstance(report_date, datetime):
        report_date = report_date.strftime('%Y-%m-%d')
    elif type(report_date) != str or report_date == "":
        new_date = datetime.now(timezone.utc).astimezone(tz.gettz('Mountain Standard Time')).strftime('%Y-%m-%d')
        logging.warning(f"Invalid date entered ('{report_date}'), defaulting to the current date ({new_date})")
        report_date = new_date
        

    # calls the Reporting API on each of the target locations, adding the JSON responses to a list
    logging.debug(f"attempting to get Bite API info for {[*desired_locations]}")
    response_list = {}
    for location_name in desired_locations:
        response_list[location_name] = {}
        ####################################### PROBLEM #################################################
        
        # TODO: Store Location ID's in an info file (UPDATED BY SEPERATE APP)
        logging.debug(f"attempting to get ID for location {location_name}")
        if location_ids.get(location_name) is None:
            logging.info(f"no ID found in bite_location_ids.json for location {location_name}")
        else:
            for channel in location_ids.get(location_name):
                # logging.debug(f"retrieving order data for {location_name} ({channel['channel']}) from Bite API", {"report_date": report_date,
                #                                                                         "channel_type": channel["channel"],
                #                                                                         "channel_id": channel["id"]})
                curr_id = channel["id"]  # gets the ID of the locations that we are generating the reports for
                curr_page = 0

                curr_response = get_reporting_data(curr_id, report_date, page_number=curr_page)  # gets the Reporting API JSON response
                # repeat until no data was returned in the response for the current page
                while len(curr_response['data']) > 0:
                    if channel["channel"] not in response_list[location_name].keys():
                        response_list[location_name].update({channel["channel"]: curr_response})   # adds the response to the dictionary of JSON responses
                    else:
                        response_list[location_name][channel["channel"]]['data'] = \
                                response_list[location_name][channel["channel"]]['data'] + \
                                curr_response['data']

                    # get the next page of data
                    curr_page += 1  
                    curr_response = get_reporting_data(curr_id, report_date, page_number=curr_page)  # gets the Reporting API JSON response
            
            ####################################### PROBLEM #################################################
    
    return response_list

def get_reporting_data(report_location_id: str, 
                       report_date = datetime.now(timezone.utc).astimezone(tz.gettz('Mountain Standard Time')), 
                       page_number = 0) -> json:
    """
    Queries the Bite Reporting API to generate a report containing data on all order placed at a location on a given day.
    By default, the report is generated for the current day.

    Parameters
    ------------
        report_location_id: String
            The Bite location ID for the site whose report you want to generate

        report_date: String
            The date for which the report will be generated

        page_number: Int
            The page of the report you want to receive for the current day
        
    Returns
    ------------
        response: JSON object
            The JSON data from the response object generated by calling the Reporting API with the given location ID

    Dependencies
    ------------
        from .reference.bite_info :
            CONTENT_TYPE, 
            X_MD_API_VERSION, 
            AUTHORIZATION_TOKEN, 
            REPORTING_PAGE_VALUE, 
            REPORTING_LIMIT_VALUE
    """

    # defines headers parameters
    req_headers = {'Content-Type': CONTENT_TYPE, 'x-md-api-version': X_MD_API_VERSION,
                   'Authorization': AUTHORIZATION_TOKEN}

    time_string = report_date.strftime('%Y-%m-%d') if type(report_date) == datetime else str(report_date)

    # defines the payload parameters
    payload = {
        "locationId": report_location_id,  # <string (PropertyId)> The Bite ID of the location.
        "date": time_string,  # <string> The date of the orders to retrieve in a YYYY-MM-DD format
        "page": page_number,  # <int32> >= 0
        "limit": REPORTING_LIMIT_VALUE}  # <int32> [1 ... 50]

    try:
        response = req.post("https://admin.getbite.com/api/v2/reporting/orders/day",
                            headers=req_headers,
                            json=payload)
        return response.json()
    except Exception as ex:
        (exception_type, exception_value, exception_traceback) = sys.exc_info()
        logging.exception(f"unknown exception thrown while accessing Bite 'Reporting' API: exception=({ex})")

        return None



##############################################################################
def get_location_data():
    """
        Queries the Bite "Get All Locations" API and returns the JSON output.

    Returns
    ----------
    response: JSON object
        The JSON output of the Bite "Get All Locations" API
    """

    # defines headers parameters
    req_headers = {'Content-Type': CONTENT_TYPE,
                   'x-md-api-version': X_MD_API_VERSION,
                   'Authorization': AUTHORIZATION_TOKEN}

    # defines the payload parameters
    locations_query = {
        "page": LOCATIONS_PAGE_VALUE,  # <int32> >= 0
        "limit": LOCATIONS_LIMIT_VALUE}  # <int32> [1 ... 50]

    try:
        # logging.debug(f"getting location data from Bite 'Get All Locations' API")
        response = req.get("https://admin.getbite.com/api/v2/locations",
                           headers=req_headers,
                           params=locations_query)
        return response.json()
    except Exception as ex:
        (exception_type, exception_value, exception_traceback) = sys.exc_info()
        logging.exception(f"exception thrown while accessing Bite 'Get All Locations' API: exception=({ex})")
        return None


def update_locations_dictionary():
    # Get a JSON list of all locations using the Locations API
    locations_json = get_location_data()

    if not locations_json["success"]:
        logging.error(f"failed to access Bite's 'LocationsGetAll' API endpoint: response=({locations_json})")
        raise Exception("failed to access Bite's 'LocationsGetAll' API endpoint")
    elif len(locations_json["data"]) == 0:
        logging.error(f"Bite's 'LocationsGetAll' API endpoint returned no data: response=({locations_json})")
        raise Exception("Bite's 'LocationsGetAll' API endpoint returned no data")

    new_locations_dictionary = {}
    for site in locations_json["data"]:
        if site["name"] not in new_locations_dictionary:
            new_locations_dictionary[site["name"]] = [{"channel":site["orderChannel"], "id":site["_id"]}]
        else:
            new_locations_dictionary[site["name"]].append({"channel":site["orderChannel"], "id":site["_id"]})

    # inputs the values to the file
    with open("../Reference/bite_location_ids.json", "w") as dict_file:
        json.dump(new_locations_dictionary, dict_file)
    return

