import sys
from .._Reference.ndjson_logging import setup_logging
from .._HelperFunctions import pull_bite_data_helpers as bite
from .._HelperFunctions import parse_data_helpers as parse
from .._CustomClasses.DatabaseObject import DatabaseObject
from datetime import *
from dateutil import tz

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


TARGET_LOCATIONS = ["Choices", "Creamery Marketplace", "Cloned - Creamery Market"] # this list specifies which locations we want order data from

# main function
def app():

    # sets up the logger
    log = setup_logging(__name__, log_to_file=False)

    # check python version
    # this is needed because Auzre Functions only allows Python 3.7 - 3.9, meaning
    # that code written for 3.10 could potentially break
    PY_VER = sys.version_info
    if PY_VER[0] != 3 or PY_VER[1] not in range(7, 10):  # range(7,10) == [7,8,9]
        log.CRITICAL(f"Using Python {PY_VER[0]}.{PY_VER[1]}, which is not supported by Azure Functions")
        return


    ############# BITE SECTION #############    

    # Retrieve the order data
    # TODO: Store Location ID's in an info file (UPDATED BY SEPERATE APP)

    # retrieves a list of JSON responses from each location
    # calls bite_data.py/get_order_data()
    
    local_tz = tz.gettz('Mountain Standard Time')

    try:
        #report_date = "2022-12-07"  # (str "YYYY-MM-DD") the date to pull the orders from. Defaults to the current date.
        report_date = datetime.now(timezone.utc).astimezone(local_tz).strftime('%Y-%m-%d')  
        order_data = bite.get_order_data(TARGET_LOCATIONS, report_date)
    except Exception as ex:
        log.error(f"could not retrieve Bite data")
        return
    
    # this array is used to store the bite_order_id's of the orders that were successfully added earlier today to the database PREVIOUS to this run of the function
    # orders_added_today = get_orders_added_today_list()

    # this array is used to store the ReportOrder obj's produced when each Report obj is initialized
    overall_order_array = []

    # this array is used to store the bite_order_id's of the orders that are successfully added to the database during THIS RUN of the function
    # sucessfully_added_order_array = []

    ############# PARSING SECTION #############

    for site in order_data:
        for channel in order_data[site]:  # inner try catches exceptions while trying to parse the JSON into classes
            try:
                log.debug(f"attempting to parse report for {site} ({channel})")
                curr_report = order_data[site][channel]
                curr_orders = parse.parse_report_into_orders(curr_report)
                overall_order_array.extend(curr_orders)

            except ValueError as ex:
                log.error(f"exception thrown while parsing reports into classes", {'exception': ex})

    orders_successfully_inserted_num = 0
    items_successfully_inserted_num = 0

    ############# DATABASE SECTION #############
    my_db = DatabaseObject()
    try:
        log.debug(f"{len(overall_order_array)} valid orders found")

        if len(overall_order_array) > 0:
            # log.debug(f"Connecting to the database")
            my_db.get_connection()

            if my_db.connected:
                # log.debug(f"adding orders to db")
                for order in overall_order_array:
                    log.debug(f"attempting to add order {order.bite_order_id}")
                    add_successful = my_db.add_order(order)
                    if add_successful:
                        orders_successfully_inserted_num += 1
                        # retrieves the ID of the order you just added, so you can link the order items to it
                        # log.debug("attempting to retrieve primary key for order", {'bite_order_id': order.bite_order_id})
                        order_key = my_db.get_order_primary_key(order.bite_order_id)

                        # sucessfully_added_order_array.append(bite_order_id)

                        for order_item in order.items:
                            # log.debug(f"attempting to add order item", {"bite_order_id": order.bite_order_id, "order_key":order_key, "item":order_item.to_dict()})
                            my_db.add_order_item(item=order_item,
                                                order_key=order_key)
                            items_successfully_inserted_num += 1
                log.debug(f"succesfully inserted {orders_successfully_inserted_num} orders and {items_successfully_inserted_num} items")
        else:
            log.debug("skipped database inserts because no valid orders found")
    except Exception as ex:
        log.error(f"exception thrown while adding orders to database", {'exception': ex})
    
    # adds all successfull orders to the list of orders added today
    # add_orders_to_orders_added_today_list()


    # log.debug(f"updating timestamp in database")
    try:
        my_db.get_connection()
        my_db.update_timestamp(GEN_LAST_UPDATED_TIMESTAMP_ID)
    except Exception as ex:
        log.error(f"exception thrown while updating LastUpdatedDatetime", {'exception': ex})
    finally:
        # manually closes the connection (shouldn't be neccessary, but couldn't hurt)
        my_db.close_connection()
    log.debug(f"EXIT fulfillment_app")
    return

# def add_orders_to_orders_added_today_list(bite_order_ids: list[str]) -> None:
#     with open(ORDERS_ADDED_TODAY_FILE_NAME, "-a") as write_file:
#         write_file.writelines(bite_order_ids)
#     return

# def get_orders_added_today_list() -> list:
#     id_list = []
#     with open(ORDERS_ADDED_TODAY_FILE_NAME, "-r") as read_file:
#         for line in read_file.readlines():
#             id_list.append(id)
#     return id_list