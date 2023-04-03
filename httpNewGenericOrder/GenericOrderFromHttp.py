import sys
import json
import logging
from .._Reference.ndjson_logging import setup_logging
from .._HelperFunctions import pull_bite_data_helpers as bite
from .._HelperFunctions import parse_data_helpers as parse
from .._CustomClasses.DatabaseObject import DatabaseObject

ORDERS_ADDED_TODAY_FILE_NAME = "list_of_orders_added_today.txt"
GEN_LAST_UPDATED_TIMESTAMP_ID = 1
ORDER_TABLE_NAME = 'Orders'

########################################################################################################################
#           Cougar Crust Version
#
#           ABOUT:  This is the main script for the app. It pulls order data from the Bite API about each order placed
#           that day, parses it into classes,and then puts it into a Microsoft SQL Server database. The PowerApps
#           frontend of the Fulfilment App uses this database to display which orders are associated with each Campus
#           Pickup time spot, and what the status of each order is.
#
#           Author: Taylor West
########################################################################################################################


# main function
def new_order(request_json):

    # check python version
    # this is needed because Auzre Functions only allows Python 3.7 - 3.9, meaning
    # that code written for 3.10 could potentially break
    PY_VER = sys.version_info
    if PY_VER[0] != 3 or PY_VER[1] not in range(7, 10):  # range(7,10) == [7,8,9]
        logging.CRITICAL(f"Using Python {PY_VER[0]}.{PY_VER[1]}, which is not supported by Azure Functions")
        return

    #if request json missing 'data' field
    if 'data' not in request_json.keys():
        message = "HTTP Request missing a 'data' field"
        logging.error(message)
        raise KeyError(message)
    

    ########### PARSING SECTION ###############
    
    order_data = [request_json['data']]                 # get the actual order data from the response
                                                            # puts into an array with one item just so we can reuse 
                                                            # the helper function to parse it, which expects an array 
                                                            # of orders

    try:
        order = parse.parse_orders_helper(order_data)[0]
    except ValueError as ex:
        logging.error(f"Invalid data found while parsing order into class:\n{ex}")
        raise ex


    orders_successfully_inserted_num = 0
    items_successfully_inserted_num = 0
    duplicate_orders_found_num = 0

    ############# DATABASE SECTION #############
    my_db = DatabaseObject()
    try:
        logging.info("Attempting to connect to the Database...")
        my_db.get_connection()

        if my_db.connected:
            logging.info("Connection Successful. Attempting to add Order to database...")
            add_successful = my_db.add_order(order)
            if add_successful:
                logging.info('Order successfully Added. Retrieving Primary Key...')
                orders_successfully_inserted_num += 1
                # retrieves the ID of the order you just added, so you can link the order items to it
                # log.debug("attempting to retrieve primary key for order", {'bite_order_id': order.bite_order_id})
                order_key = my_db.get_order_primary_key(order.bite_order_id)

                logging.info('Order Primary Key retrieved successfully. Attempting to add order items.' + \
                             f'Num items found = {len(order.items)}')

                for order_item in order.items:
                    # log.debug(f"attempting to add order item", {"bite_order_id": order.bite_order_id, "order_key":order_key, "item":order_item.to_dict()})
                    my_db.add_order_item(item=order_item,
                                        order_key=order_key)
                    items_successfully_inserted_num += 1

                logging.info(f"Succesfully inserted {orders_successfully_inserted_num} orders and {items_successfully_inserted_num} items.")
        
            else:
                duplicate_orders_found_num += 1
                logging.debug(f"Order Already in Database. OrderID:{order.bite_order_id}")
        else:
            logging.debug("Skipped database inserts because no valid orders found")

        logging.info(f"{orders_successfully_inserted_num} Orders and {items_successfully_inserted_num} New Items Inserted into Database.")

    except ConnectionError as ex:
        logging.error(f"There was an issue connecting to the database:\n{ex}")
        raise ex
    
    except Exception as ex:
        logging.error(f"exception thrown while adding orders to database:\n{ex}")
    
    # adds all successfull orders to the list of orders added today
    # add_orders_to_orders_added_today_list()


    logging.info(f"Updating timestamp in database...")
    try:
        my_db.get_connection()
        my_db.update_timestamp(GEN_LAST_UPDATED_TIMESTAMP_ID)
        logging.info("Timestamp successfully updated.")
    except Exception as ex:
        logging.error(f"exception thrown while updating LastUpdatedDatetime\n{ex}")
    finally:
        # manually closes the connection (shouldn't be necessary, but couldn't hurt)
        my_db.close_connection()
    
    logging.debug(f"EXIT fulfillment_app")
    return {"num_orders_inserted":orders_successfully_inserted_num,
            "num_duplicate_orders":duplicate_orders_found_num}

