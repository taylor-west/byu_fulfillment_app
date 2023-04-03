import logging
import json
import requests
import azure.functions as func

COUG_CRUST_FUNC_URL = 'https://biteorderfulfillmentapp.azurewebsites.net/api/httpNewCougarCrustOrder?code=J7Biwt1o06asYMHZtirll6TGxmEkH0M4Mv9_97N6LHXEAzFuMvW0MA=='
GENERIC_ORDER_FUNC_URL = 'https://biteorderfulfillmentapp.azurewebsites.net/api/httpNewGenericOrder?code=YoWlyjRmvDNMvpf9xnHMOUdAo2qg1RfhdsJxglAxB_iGAzFuwPFbsQ=='
DINING_OPTIONS = ['Campus Delivery (Contactless)']
OUR_PRIVATE_KEY = ''  # this is to call 
BITE_PRIVATE_KEY = 'cfb9e5aebaff5d5142e8fd1b4ecba814471376c653ecbad69af4d93b90d4a4cd4ef9b6e15c06674fd33cee025c4e36bc6e54bc2944d711774fcadba76bad33c2'

# function to verify that the request sent in has all the fields we need
def has_required_fields(request_order_data:dict):
    required_fields = ['createTime',
                        'siteId',
                        'siteName',
                        'locationId',
                        'orderChannel',
                        'diningOption',
                        'orderId',
                        'isCancelled',
                        'orderNumber',
                        'items',
                        'guest'
                        ]
    
    has_required_fields = True
    missing_field = None
    for required_field in required_fields:
        if required_field not in request_order_data.keys():
            has_required_fields = False
            missing_field = required_field
            break
    
    return has_required_fields, missing_field


def fix_json(json_str):
    """
    Bite gives us a json in python dictionary format, which needs to be converted to normal
    json before we can parse it. Most of the strings are in single quotes, like 'text', but 
    need to be converted to be within double quotes like "text" for the json parser to work 
    correctly. The exception is if a string has a single quote in it, in which case Bite sends 
    us the string already in double quotes, like "text with a ' in it". 

    This function reads each character in the json string. When a quote, single or double is found, 
    it marks a string as opened. If the string was opened by a single quote, it replaces the single
    quotes with double quotes
    """
    new_str = ""
    open_dbl_qt = False
    open_sngl_qt = False
    for i in range(len(json_str)):
        c = json_str[i]
        if c == '"':
            a = 1
        if c == "'" and not open_dbl_qt:        #if a single quote is found and a double quote is not open

            if open_sngl_qt:                        # if a string with a single quote is already open                         
                num_escape_chars = 0
                j = i - 1    
                while j > 0 and json_str[j] == '\\':        # count how many backslashes preceed the new single quote
                    num_escape_chars += 1
                    j -= 1

                if num_escape_chars % 2 == 0:               # if an even number of backslashes, then the single quote is closing the string         
                    open_sngl_qt = not open_sngl_qt                # mark the string as closed
                    new_str += '"'                                 # replace the single quote with a double quote in the new_str
                else:                                       # otherwise the single quote is escaped within the string
                    new_str += c     
            else:                                   # otherwise the single quote is opening a new string   
                open_sngl_qt = not open_sngl_qt             # mark a new string as opened
                new_str += '"'                              # replace the single quote with a double quote in the new string                  
                  


        elif c == '"':    # otherwise, if a double quote is found
            if not open_sngl_qt and not open_dbl_qt:        # if no strings are currently open
                open_dbl_qt = not open_dbl_qt                      # double quote is opening a new string
                new_str += c     

            else:                                           # if a string is already open
                num_escape_chars = 0
                j = i - 1 
                while j > 0 and json_str[j] == '\\':            # count how many backslashes preceed the new double quote
                    num_escape_chars += 1
                    j -= 1

                if num_escape_chars % 2 == 0:                   # if there are an even number of escape characters
                    if open_sngl_qt:                                # if the string was opened with a single quote
                        new_str += '\\"'                               # the double quote was not escaped in the single quote
                                                                       # and needs to be escaped because the single quotes
                                                                       # opening and closing the string will be replaced 
                                                                       # by double quotes

                    elif open_dbl_qt:                               # However, if the string was opened by a double quote
                        open_dbl_qt = not open_dbl_qt                  # then the non-escaped double quote is closing the string
                        new_str += c    

                else:                                           # if there are an odd number of escape characters
                    new_str += c                                    # then the double quote was already escaped in the string
                                                                    # just move on to the next character
                                         
        else:
            new_str += c

    # lastly replace the python True, False, with the json versions true, false
    return new_str.replace("False", "false").replace("True", "true")


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    logging.info(f'{str(req.get_json())}')

    req_json_string = str(req.get_json())
    

    # convert the response to a json object
    #req_json_string = req.get_body().decode("utf8").strip().strip('"') \
       # .replace("\\\\", "\\").replace('\\"', '"')                          # Some stuff to fix the string because Bite sends it in a dumb format
    
    # OLD: req_json_string = req_json_string.replace("'", '"').replace("False", "false").replace("True", "true")
    
    req_json_string = fix_json(req_json_string)             # systematically replaces strings within single quotes with
                                                                # strings inside of double quotes


    req_body = json.loads(req_json_string)
    

    # make sure request has the event and data fields
    if 'event' not in req_body.keys() or 'data' not in req_body.keys():
        message = "Invalid Request. Missing either 'event' or 'data' attributes."
        
        logging.info(message)
        return func.HttpResponse(
             message,
             status_code=400
             )

    
    # make sure the event that triggered the webhook is order sent
    if req_body['event'] != 'order-sent':           # only take requests from "order-sent" webhook
        message = "Webhook request received, but event was not 'order-sent', so no actions were taken."
        
        logging.info(message)
        return func.HttpResponse(
             message,
             status_code=200
             )
    
    
    # check if order has all required fields for us to be able to process an order
    valid_order, missing_field = has_required_fields(req_body['data'])
    if not valid_order:

        message = f"Invalid Order Data Sent. Missing Field: {missing_field}"
        logging.info(message)
        return func.HttpResponse(message,
             status_code=400
             )

    # make sure dining option is one we are processing orders for
    if req_body['data']['diningOption'] not in DINING_OPTIONS:
        dining_options_string = ""
        for option in DINING_OPTIONS:
            dining_options_string = dining_options_string + f"'{option}'\n"

        message = "Webhook request received, but order was not processed because diningOption " + \
                 f"was not equal to one of the following:\n{dining_options_string}"
        
        logging.info(message)
        return func.HttpResponse(
             message,
             status_code=200
             )


    # if Dining Option is Campus Delivery but outpostDeliveryLocation field is missing
    if req_body['data']['diningOption'] == 'Campus Delivery (Contactless)':
        if 'outpostDeliveryLocation' not in req_body['data'].keys():
            message = f"Invalid Order Data Sent. Missing Field: outpostDeliveryLocation"
            logging.info(message)
            return func.HttpResponse(message,
                status_code=400
                )
        elif 'futureOrderTime' not in req_body['data'].keys():
            message = f"Invalid Order Data Sent. Missing Field: futureOrderTime"
            logging.info(message)
            return func.HttpResponse(message,
                status_code=400
                )

    ###### If Request Is Valid ######

    order_location_id = req_body['data']['locationId']

    # read in the list of order ID's
    BITE_LOCATION_IDS_FILE_URL = "./_Reference/bite_location_ids.json"
    with open(BITE_LOCATION_IDS_FILE_URL, "r") as dict_file:
        location_ids = json.load(dict_file)

    COUGAR_CRUST_SITE_NAME = 'Cougar Crust'
    OTHER_SITE_NAMES = ["Aloha Plate",
                        "BYU-testing",
                        "Choices", 
                        "Cloned - Creamery Market",
                        "Creamery Marketplace", 
                        "Papa John's",
                        "Subway",
                        "Wendy's"]                  # this list specifies which locations we want order data from



    # Get lists of Location IDs associated with Cougar Crust
    COUGAR_CRUST_LOCATION_IDS = []
    for location in location_ids[COUGAR_CRUST_SITE_NAME]:
        COUGAR_CRUST_LOCATION_IDS.append(location['id'])

    # Get List of loction IDs associated with other restaurants we are currently
     # processing orders for
    OTHER_LOCATION_IDS = []
    for site in OTHER_SITE_NAMES:
        for location in location_ids[site]:
            OTHER_LOCATION_IDS.append(location['id'])

    try:
        # Based on location ID of the order, call the appropriate function to process the order
        if order_location_id in COUGAR_CRUST_LOCATION_IDS:      # Cougar Crust Orders
            logging.info("Order is a Cougar Crust Order. Calling httpNewCougarCrustOrder Function")
            response = requests.post(url=COUG_CRUST_FUNC_URL,
                        json=req_body)


        elif order_location_id in OTHER_LOCATION_IDS:           # Other Orders
            logging.info("Order is a Generic Order. Calling httpNewGenericOrder Function")
            response = requests.post(url=GENERIC_ORDER_FUNC_URL,
                        json=req_body)
            
        
        else:   # If order is for a site we are not currently taking delivery orders for
            message = f"Order was valid but not for a site we are currently processing orders for.\n" + \
                        f"OrderID: {req_body['data']['orderId']}\n" + \
                        f"SiteName: {req_body['data']['siteName']}\n" + \
                        f"LocationID: {req_body['data']['locationId']}"
            logging.info(message)
            return func.HttpResponse(
                message,
                status_code=200
                )
        
        # Only get here if one of the Other Functions was called
        if response.status_code == 200:
            message = f"The Called Function Successfully Processed the Request.\n"
        else:
            message = "The Called Function Failed to Successfully Process the Request\n"
        
        message = message + f"STATUS_CODE: {response.status_code}\n" + \
                            f"Message: {response.text}"
        logging.info(message)
        return func.HttpResponse(
                message,
                status_code=200
                )
    
    except Exception as ex:
        logging.error(ex)
        message = "An unknown error occurred while processing the request."
        return func.HttpResponse(
                message,
                status_code=500
                )
