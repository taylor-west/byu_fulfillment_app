import json
import datetime
import sys
import requests as req

import logging
from .._Reference.bite_info import CONTENT_TYPE, X_MD_API_VERSION, AUTHORIZATION_TOKEN
from .._Reference.bite_info import LOCATIONS_PAGE_VALUE, LOCATIONS_LIMIT_VALUE
from .._Reference.bite_info import REPORTING_PAGE_VALUE, REPORTING_LIMIT_VALUE

########################################################################################################################
#           ABOUT:  This script pulls data from the Bite API about every order placed that day for a specified list of
#           locations. It is used in the Campus Pickup Fulfillment App by BYU Dining Services.
#           
#           Authors: Taylor West
#           
#           BITE API documentation can be found here: https://documentation.getbite.com/
########################################################################################################################

# sets up the logger
# log = setup_logging(__name__, log_to_file=False)

def get_order_data(desired_locations: list, report_date: str = str(datetime.date.today())) -> dict:
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
    # makes sure that we have a valid date
    if isinstance(report_date, datetime.date):
        report_date = str(report_date)
    elif report_date is None or report_date == "":
        logging.warning(f"Invalid date entered ('{report_date}'), defaulting to the current date ({str(datetime.date.today())})")
        report_date = str(datetime.date.today())

    # read in the list of order ID's
    with open("./_Reference/bite_location_ids.json", "r") as dict_file:
        location_ids = json.load(dict_file)

    # calls the Reporting API on each of the target locations, adding the JSON responses to a list
    logging.debug(f"will attempt to get Bite API info for the following locations: {[*desired_locations]}")
    response_list = {}
    for location_name in desired_locations:
        response_list[location_name] = {}
        
        # TODO: Store Location ID's in an info file (UPDATED BY SEPERATE APP)
        logging.debug(f"attempting to get ID for location {location_name}")
        if location_ids.get(location_name) is None:
            logging.debug(f"no ID found in bite_location_ids.json for location {location_name}")
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
    
    return response_list

def get_reporting_data(report_location_id: str, 
                       report_date: datetime.date = datetime.date.today(), 
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

    # defines the payload parameters
    payload = {
        "locationId": report_location_id,  # <string (PropertyId)> The Bite ID of the location.
        "date": str(report_date),  # <string> The date of the orders to retrieve in a YYYY-MM-DD format
        "page": page_number,  # <int32> >= 0
        "limit": REPORTING_LIMIT_VALUE}  # <int32> [1 ... 50]

    try:
        response = req.post("https://admin.getbite.com/api/v2/reporting/orders/day",
                            headers=req_headers,
                            json=payload)
        return response.json()
    except Exception as ex:
        (exception_type, exception_value, exception_traceback) = sys.exc_info()
        logging.exception(f"unknown exception thrown while accessing Bite 'Reporting' API: {ex}")

        return None
