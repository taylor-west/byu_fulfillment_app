import sys # to determine what version of python we are using
import datetime # use today() to get current date

# from .._Reference.ndjson_logging import setup_logging
import logging as logging
from . import ccr_bite_data as bite
from . import ccr_parse_data as ccr_parse
from .._HelperFunctions import parse_data_helpers as parse
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
def new_order(request_json) -> None:
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
    
    #if request json missing 'data' field
    if 'data' not in request_json.keys():
        message = "HTTP Request missing a 'data' field"
        logging.error(message)
        raise KeyError(message)
    
    ############# END SETUP SECTION #############
    


    ############# PARSING SECTION #############
    # creates the Databse object
        # initialize here instead of the Database Section because it will be used in
        # get_orders_added_today_list(), which is called in the initialization of 
        # orders_added_today, which is located in the Bite Section. 

    ccr_db = CougCrustDBObject()

    # Get POS_IDS for items that are pizzas
    try:
        logging.info("Attempting to pull list of Pizza PosIDs")
        ccr_db.get_connection()
        pizza_pos_ids = ccr_db.get_pizza_pos_ids() 
        logging.info(f"{len(pizza_pos_ids)} Pizza PosIDs found")              
        
    except Exception as ex:
        message = f'Error while attempting to retrieve list of Pizza PosIDs (problem connecting to the Database):'
        logging.error(f'{message}:\n\n{ex}')
        raise ConnectionError(message)
    
    finally:
        ccr_db.close_connection()

    # pull the order info json out of the request body
    order_data = [request_json['data']]                 # get the actual order data from the response
                                                            # puts into an array with one item just so we can reuse 
                                                            # the helper function to parse it, which expects an array 
                                                            # of orders

    # define a function for parsing the order items using the current list of pizza pos_ids                                                         
    ccr_order_item_func = lambda report: ccr_parse.ccr_parse_order_items(report, pizza_pos_ids)     

    # parse the order into an BiteOrder Object using the ccr_order_item_func to parse the order
        # items into CougarCrustOrderItem objects instead of just BiteOrderItem objects
    order = parse.parse_orders_helper(order_data, ccr_order_item_func)[0]           # the parse function returns a list of
                                                                                # order objects that were just created. 
                                                                                # Should only have one in it, so simply
                                                                                # grabs the first


    orders_successfully_inserted_num = 0
    items_successfully_inserted_num = 0
    duplicate_orders_found_num = 0

    ############# END PARSING SECTION #############



    ############# DATABASE SECTION #############
    try:
        logging.info("Attempting to connect to the Database...")
        ccr_db.get_connection()

        if ccr_db.connected:
            logging.info("Connection Successful. Attempting to add Order to database...")
            add_successful = ccr_db.add_order(order)
            if add_successful:
                # retrieves the ID of the order you just added, so you can link the order items to it
                logging.info('Order successfully Added. Retrieving Primary Key...')
                orders_successfully_inserted_num += 1
                order_key = ccr_db.get_order_primary_key(order.bite_order_id)

                logging.info('Order Primary Key retrieved successfully. Attempting to add order items.' + \
                             f'Num items found = {len(order.items)}')

                num_pizzas = 0
                for order_item in order.items:
                    # log.debug(f"attempting to add order item", {"bite_order_id": order.bite_order_id, "order_key":order_key, "item":order_item.to_dict()})
                    ccr_db.add_order_item(item=order_item,
                                        order_key=order_key)
                    items_successfully_inserted_num += 1

                    if order_item.is_pizza:
                        num_pizzas += 1

                logging.info(f"Items successfully added. {num_pizzas} were pizzas. Updating pizza count " + \
                             f"for order {order_key} in Database")
                # update order with the number of pizzas
                ccr_db.update_pizza_count(order_key, num_pizzas)
                logging.info("Order num pizzas successfully updated")

            else:
                duplicate_orders_found_num += 1
        else:
            logging.info("Skipped database inserts because no valid orders found")

        logging.info(f"{orders_successfully_inserted_num} Orders and {items_successfully_inserted_num} New Items Inserted into Database.")

    except ConnectionError as ex:
        logging.error(f"There was an issue connecting to the database:\n{ex}")
        raise ex

    except Exception as ex:
        logging.error(f"There was an unknown issue while attempting to insert order or items into the Database\n{ex}")
        raise ex

    



    logging.info(f"Updating timestamp in database...")
    try:
        ccr_db.get_connection()
        ccr_db.update_timestamp(CCR_LAST_UPDATED_TIMESTAMP_ID)
        logging.info("Timestamp successfully updated.")
    except Exception as ex:
        logging.error(f"exception thrown while updating LastUpdatedDatetime:\ {ex}")
        raise ex
    finally:
        # manually closes the connection (shouldn't be neccessary, but couldn't hurt)
        ccr_db.close_connection()

    ############# END DATABASE SECTION #############

    logging.debug("EXIT fulfillment_app")
    return {"num_orders_inserted":orders_successfully_inserted_num,
            "num_duplicate_orders":duplicate_orders_found_num}
