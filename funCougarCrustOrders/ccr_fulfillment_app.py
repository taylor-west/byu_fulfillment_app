import sys # to determine what version of python we are using
from datetime import * # use today() to get current date
from dateutil import tz

# from .._Reference.ndjson_logging import setup_logging
import logging as logging
from .._HelperFunctions import pull_bite_data_helpers as bite
from . import ccr_parse_data as parse
from .ccr_db_object import CougCrustDBObject

ORDERS_ADDED_TODAY_FILE_NAME = "list_of_orders_added_today.txt"
CCR_LAST_UPDATED_TIMESTAMP_ID = 2
ORDER_TABLE_NAME = 'CougarCrustOrders'
TARGET_LOCATIONS = ["Cougar Crust"]  # this list specifies which locations we want order data from

########################################################################################################################
#           Pulls Orders for CougarCrust and Blue-Ribbon Box
#
#           ABOUT:  This is the main script for the app. It pulls order data from the Bite API about each order placed
#           that day, parses it into classes,and then puts it into a Microsoft SQL Server database. The PowerApps
#           frontend of the Fulfilment App uses this database to display which orders are associated with each Campus
#           Pickup time spot, and what the status of each order is.
#
#           Author: Taylor West
########################################################################################################################


# main function
def app() -> None:
    """
    This function defines the main flow of the app. It sets up a logger, pulls order data from the Bite API, parses and filters the data, and then inputs the orders to the database.
    
    Functions Referenced
    ------------

        reference/ndjson_logging.py
            
                setup_logging()

        CougCrustDBObject.py/CougCrustDBObject
            
                ._init_()

                .get_connection()

                .get_pizza_pos_ids()

                .close_connection()

                .add_order()

                .get_order_primary_key()

                .add_order_item()

                .update_pizza_count()

                .update_timestamp()

        ccr_bite_data.py
        
                get_order_data()
    

        ccr_parse_data.py
                
                ccr_parse_report_into_orders()
    
    """
    
    ############# SETUP SECTION #############    
    # check python version
        # Auzre Functions only allows Python 3.7 - 3.9, meaning that code written
        # for Python 3.10+ could potentially break
    PY_VER = sys.version_info
    if PY_VER[0] != 3 or PY_VER[1] not in range(7, 10):  # range(7,10) == [7,8,9]
        logging.CRITICAL(f"Using Python {PY_VER[0]}.{PY_VER[1]}, which is not supported by Azure Functions")
        return
    ############# END SETUP SECTION #############


    ############# BITE SECTION #############    

    # Retrieve the order data

    # retrieves a list of JSON responses from each location
    # calls bite_data.py/get_order_data()

    local_tz = tz.gettz('US/Mountain')
    
    try:
        report_date = datetime.now(timezone.utc).astimezone(local_tz)
        logging.info(f'Time retrieved by Azure, converted to local time {str(report_date)}')
        report_date = report_date.strftime('%Y-%m-%d')                  # (str "YYYY-MM-DD") the date to pull the orders from.
        order_data = bite.get_order_data(TARGET_LOCATIONS, report_date) # Defaults to the current date if no date provided.
    except Exception as ex:
        logging.error(f"could not retrieve Bite data", {'exception': ex})
        return
    
    # stores the ReportOrder obj's produced when each Report obj is initialized
    overall_order_array = []

    # stores the bite_order_id's of the orders that were successfully added to the database EARLIER today (already in when this run of the function starts)
    #   calls get_orders_added_today_list(), which reads the list in from an external file
    # orders_added_today = get_orders_added_today_list() # TODO: use when implementing redundancy reduction

    # this array is used to store the bite_order_id's of the orders that are successfully added to the database during THIS RUN of the function
    # sucessfully_added_order_array = [] # TODO: use when implementing redundancy reduction

    ############# END BITE SECTION #############    



    ############# PARSING SECTION #############
    # creates the Databse object
        # initialize here instead of the Database Section because it will be used in
        # get_orders_added_today_list(), which is called in the initialization of 
        # orders_added_today, which is located in the Bite Section. 
    ccr_db = CougCrustDBObject()

    # Get POS_IDS for items that are pizzas
    ccr_db.get_connection()
    pizza_pos_ids = ccr_db.get_pizza_pos_ids()               
    ccr_db.close_connection()

    # Parse Orders and OrderItems into appropriate classes
    for site in order_data:
        for channel in order_data[site]:  # inner try catches exceptions while trying to parse the JSON into classes
            try:
                logging.debug(f"attempting to parse report for {site} ({channel})")
                curr_report = order_data[site][channel]
                curr_orders = parse.ccr_parse_report_into_orders(curr_report, pizza_pos_ids)
                overall_order_array.extend(curr_orders)
            except ValueError as ex:
                logging.error(f"exception thrown while parsing reports into classes: {ex}")

    orders_successfully_inserted_num = 0
    items_successfully_inserted_num = 0
    num_duplicates = 0

    ############# END PARSING SECTION #############



    ############# DATABASE SECTION #############
    try:
        logging.info(f"{len(overall_order_array)} orders retrieved from Bite")

        if len(overall_order_array) > 0:
            # log.debug(f"Connecting to the database")
            ccr_db.get_connection()

            if ccr_db.connected:
                # log.debug(f"adding orders to db")
                for order in overall_order_array:
                    logging.debug(f"attempting to add order {order.bite_order_id}")
                    add_successful = ccr_db.add_order(order)
                    if add_successful:
                        orders_successfully_inserted_num += 1
                        # retrieves the ID of the order you just added, so you can link the order items to it
                        # log.debug("attempting to retrieve primary key for order", {'bite_order_id': order.bite_order_id})
                        order_key = ccr_db.get_order_primary_key(order.bite_order_id)

                        # sucessfully_added_order_array.append(bite_order_id)

                        num_pizzas = 0
                        for order_item in order.items:
                            # log.debug(f"attempting to add order item", {"bite_order_id": order.bite_order_id, "order_key":order_key, "item":order_item.to_dict()})
                            ccr_db.add_order_item(item=order_item,
                                                order_key=order_key)
                            items_successfully_inserted_num += 1

                            if order_item.is_pizza:
                                num_pizzas += 1

                        # update order with the number of pizzas
                        ccr_db.update_pizza_count(order_key, num_pizzas)
                    else:
                        num_duplicates += 1

                logging.info(f"{orders_successfully_inserted_num} orders and {items_successfully_inserted_num} items inserted into database. {num_duplicates} duplicate orders found.")
        else:
            logging.info("skipped database inserts because no valid orders found")
    except Exception as ex:
        logging.error(f"exception thrown while adding orders to database: {ex}")
    
    # adds all successfull orders to the list of orders added today
    # add_orders_to_orders_added_today_list()


    # log.debug(f"updating timestamp in database")
    try:
        ccr_db.get_connection()
        ccr_db.update_timestamp(CCR_LAST_UPDATED_TIMESTAMP_ID)
    except Exception as ex:
        logging.error(f"exception thrown while updating LastUpdatedDatetime {ex}")
    finally:
        # manually closes the connection (shouldn't be neccessary, but couldn't hurt)
        ccr_db.close_connection()

    ############# END DATABASE SECTION #############

    logging.debug("EXIT fulfillment_app")
    return
