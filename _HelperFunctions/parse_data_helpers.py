import sys
from dateutil.parser import isoparse
from datetime import *
from .._Reference.db_info import KEYS, DINING_OPTION_CONVERSIONS
from .._Reference.bite_info import OUTPOST_DINING_OPTION_NAME
from .._CustomClasses.CustomExceptions import *
from .._CustomClasses.BiteOrder import BiteOrder
from .._CustomClasses.BiteOrderItem import *


#### Helper Function #####
def parse_orders_helper(order_list, parse_order_items_func=None):
    """
    Takes an array of orders in json format as returned from Bite and puts them into BiteOrder objects
    
    Parameters:
    ------------------------
    order_list: The list of json objects

    parse_order_items: Optional function for parsing custom order item types
                       Should be defined as follows:

                        def function(list_of_order_items):
                           Params:
                            list_of_order_items: list of order item json objects

                           Return:
                            list of type BiteOrderItem (or subclass)

    -------------------------

    Return: List of BiteOrders
    
    """

    report_order_objects = []
    for curr_order in order_list:
        try:
            # checks diningOption to see if we even need to add this order to the list
            # logging.debug("checking if we need to add this order (based on diningOption)",
            #           {"bite_order_id": curr_order["orderId"]})

            dining_option = curr_order["diningOption"]
            bite_order_id = curr_order["orderId"]

            if dining_option not in DINING_OPTION_CONVERSIONS.keys():
                #logging.debug(f"skipping order (diningOption not in list of desired options)",
                #          {"diningOption": curr_order["diningOption"], "bite_order_id": curr_order["orderId"]})
                continue

            # makes sure that we have a valid delivery address or location
            delivery_address = curr_order["deliveryAddress"] if "Catering" in curr_order[
                "diningOption"] else None

            outpost_location = curr_order["outpostDeliveryLocation"] if (dining_option == OUTPOST_DINING_OPTION_NAME) else None  # this only shows up on Campus Delivery orders
            logging.debug(f"pre-checking delivery constraint: diningOption='{dining_option}', delivery_address='{delivery_address}', outpost_location='{outpost_location}'")
            
            if  (delivery_address is None) and (outpost_location is None):
                logging.exception(f"order does not have delivery information: delivery_address='{delivery_address}', outpost_location='{outpost_location}'")
            else:
                logging.debug("delivery constraint valid")


            #get phone number 
            guest_phone = curr_order["guest"]["phoneNumber"] if "phoneNumber" in curr_order[
                "guest"].keys() else None
            
            # get special note if there is one
            order_note = order_list[
                "note"] if "note" in curr_order.keys() else None # I'm honestly not even sure if orders can have notes

            ## -- create order items array -- ##
            if parse_order_items_func is not None:
                order_items = parse_order_items_func(curr_order["items"])
            else:
                order_items = curr_order["items"]         # if no function is provided to parse
                                                          # the order items, the array of raw json
                                                          # objects will be passed and parsed by
                                                          # the BiteOrder object itself, into normal
                                                          # BiteOrderItem objects.

            ## -- creates the ReportOrder obj -- ##
            curr_order_obj = BiteOrder(bite_order_id     = curr_order["orderId"],
                                       order_num         = curr_order["orderNumber"],
                                       origin_site       = curr_order["siteName"],
                                       created_date      = curr_order["createTime"],
                                       ready_date        = curr_order["futureOrderTime"],
                                       dining_option     = curr_order["diningOption"],
                                       guest_email       = curr_order["guest"]["email"],
                                       guest_id          = curr_order["guest"]["guestId"],
                                       order_items_array = order_items,
                                       guest_phone       = guest_phone,
                                       outpost_location  = outpost_location,
                                       delivery_address  = delivery_address,
                                       is_cancelled      = curr_order["isCancelled"],
                                       order_note        = order_note)

            report_order_objects.append(curr_order_obj)
            logging.debug("order successfully added to order_list")

        except BadDiningOption:
            logging.warning("invalid Dining Option")
        except ValueError as ex:
            (exception_type, exception_value, exception_traceback) = sys.exc_info()
            logging.exception(f"ValueError exception raised while adding order to report: bite_order_id='{bite_order_id}', exception=({ex})")
        except Exception as ex:
            (exception_type, exception_value, exception_traceback) = sys.exc_info()
            logging.exception(f"exception raised while parsing order from report: bite_order_id='{bite_order_id}', exception=({ex})")

    return report_order_objects




##################################################################
#### Main function for parsing the report into Order Objects #####
##################################################################
def parse_report_into_orders(report_dict: dict, parse_order_item_func = None) -> list[BiteOrder]:
    """
    Parses the report JSON produced by the Bite API response for each site into an array of ReportOrder objects.
    Note that this does not clean up the inputs from the json, and simply passed them along. Data cleaning is done
    in the Order class initializer.

    Parameters
    ------------
    report_dict: dict
        The report produced by making a query to the Bite API for a single site, formatted as a dictionary

    Returns
    ------------
    report_orders_objects: list[Order]
        A list of all Order objects produced while parsing this report
    """
    # validates that we can a correctly formatted input
    if not isinstance(report_dict, dict):
        raise ValueError("the given report was of the wrong datatype (supposed to be dict)")

    # makes sure that the API request we successfully processed
    if "success" in report_dict.keys() and not report_dict["success"]:
        raise ValueError("this api request didn't yield a valid result")

    # makes sure that we can access the data
    if "data" not in report_dict.keys() or not isinstance(report_dict["data"], list):
        raise ValueError("the report json is improperly formatted (does not have a valid 'data' field)")


    if report_dict["data"]:  # checks if there are any order to process
        order_list = report_dict["data"]  # the orders should be stored as a list or dictionaries
        logging.info(f"parsing orders for {order_list[0]['siteName']} ({len(order_list)} orders found)")

        # this list stores all Order objects that we parsed from the report_dict
        return parse_orders_helper(order_list, parse_order_item_func)

        # create a ReportOrder object for each order in the "data" array
        
    else:
        logging.info("No orders found in this report")

