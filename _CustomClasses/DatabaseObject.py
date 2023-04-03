from datetime import datetime
from dateutil.parser import isoparse
import sys
import pyodbc
import logging

from .._Reference.db_info import SERVER_NAME, DATABASE_NAME, DRIVER, DB_USERNAME, DB_PASSWORD, KEYS
from .._CustomClasses.BiteOrder import *
from .._CustomClasses.BiteOrderItem import *


class DatabaseObject:
    def __init__(self) -> None:
        self.connected = False
        self.connection = None

        logging.debug("created Database object")
        return

    def get_connection(self) -> None:
        """
        a singleton method that retrieves a new connection to the database or returns the active connection
        :return:
        """
        # this is a singleton
        if self.connection is None:
            try:
                self.make_new_db_connection()
            except Exception as ex:
                (exception_type, exception_value, exception_traceback) = sys.exc_info()
                if exception_value.args[0] == str(42000):
                    logging.error(f"current IP address is not authorized to connect to the database: exception=({ex})")
                    self.connected = False
                else:
                    logging.exception(f"could not connect to the database: exception=({ex})")
                    raise ex
        else:
            logging.debug("using existing database connection")
        return

    def close_connection(self) -> None:
        """
        Manually closes any open connections to the databse
        """
        try:
            if self.connected:
                self.connection.close()
                self.connection = None
                self.connected = False
                logging.debug("database connection successfully closed")
        except Exception as ex:
            (exception_type, exception_value, exception_traceback) = sys.exc_info()
            logging.error(f"exception thrown while attempting to close database connection: exception=({ex})")        
        return

    def make_new_db_connection(self) -> None:
        """
        Gets a database connection using the information found in main/reference/db_info.py.

        :return: None
        """
        connection_string = f"DRIVER={DRIVER};SERVER=tcp:{SERVER_NAME};PORT=1433;DATABASE={DATABASE_NAME};UID={DB_USERNAME};PWD={DB_PASSWORD}"
        # print("\n\nconnection string:\n", connection_string, "\n\n")
        # logging.debug(f"attempting to get new database connection",
        #           {'connection_string': connection_string, 'driver': DRIVER, 'server': f"tcp:{SERVER_NAME}",
        #            'port': 1433, 'database': DATABASE_NAME})
        self.connection = pyodbc.connect(connection_string)
        # self.connection = pyodbc.connect('DRIVER=' + DRIVER + ';SERVER=tcp:' + SERVER_NAME + ';PORT=1433;DATABASE=' + DATABASE_NAME + ';UID=' + DB_USERNAME + ';PWD=' + DB_PASSWORD)

        self.connected = True

        logging.debug("database connection successful")
        return

    def add_order(self, order: BiteOrder, db_table_name:str = 'Orders', exclude_fields=[]) -> bool:
        """
        Inserts an order into the Orders table of the database. If ends up being faster to just attempt an insert and catch the exception if the order already exists in the database, instead of trying to check beforehand if the order already exists. Returns a bool reflecting whether the insert was successful.
        :param order: Order object containing the data to insert into the database
        :return: (bool) whether the order was successfully inserted or not
        """
        # logging.debug("adding order", {'order': order.to_dict()})

        fields = {"BiteOrderID": order.bite_order_id, 
                  "BiteOrderNum": order.orderNum, 
                  "CreatedDate": order.created_date,
                  "DiningOption": order.dining_option_id, 
                  "OriginSiteID": order.origin_site_id, 
                  "OutpostLocationID": order.outpost_location_id,
                  "ReadyDate": order.ready_date, 
                  "GuestID": order.guest_id, 
                  "GuestEmail": order.guest_email, 
                  "GuestPhone": order.guest_phone,
                  "FulfillmentStatus": order.fulfillment_status_id, 
                  "DeliveryAddress": order.delivery_address}
        
        # make fields string for query
        order_db_field_names = "("
        insert_field_values = []
        for field in fields:
            if field not in exclude_fields:
                order_db_field_names += f'{field} '
                insert_field_values.append(fields[field])
            
        order_db_field_names = order_db_field_names.strip() + ")"
        order_db_field_names = order_db_field_names.replace(" ", ", ")
        
        sql_insert_query_args = tuple(insert_field_values)
        with self.connection.cursor() as cursor:
            try:

                sql_insert_query_statement = f"""INSERT INTO [dbo].[{db_table_name}] {order_db_field_names} 
                                                 VALUES ({'?, ' * (len(sql_insert_query_args) - 1)}?)"""

                cursor.execute(sql_insert_query_statement, sql_insert_query_args)
                logging.info(f"Order successfully added to db - {order.bite_order_id}")
            except pyodbc.IntegrityError as ex:
                if ex.args[0] == '23000':
                    logging.info(f"Order already exists in DB - {order.bite_order_id}: exception=({ex})")
                    return False
            except Exception as other_ex:
                # (exception_type, exception_value, exception_traceback) = sys.exc_info()
                # logging.debug("order insert failed", {'exception': {"exception_type": exception_type, "exception_value": exception_value}, 'order': order.to_dict()})
                logging.info(f"Order insert failed: bite_order_id='{order.bite_order_id}', exception=({other_ex})")
                return False
        return True

    def add_order_item(self, item: BiteOrderItem, order_key: int) -> None:
        # logging.debug(f"adding order item", {'order_key': order_key, 'item': item.to_dict()})

        value_fields = "(OrderID, \
                        ItemName, \
                        ModString, \
                        Quantity, \
                        SpecialNote \
                        )"

        item_values = (order_key,
                        item.name,
                        item.mod_string,
                        item.quantity,
                        item.note)

        with self.connection.cursor() as cursor:
            try:
                cursor.execute(f"INSERT INTO dbo.OrderItems {value_fields} VALUES (?, ?, ?, ?, ?)", item_values)
                logging.info(f"item added: parent_order_pk='{order_key}', item=({item.to_dict()})")
            except pyodbc.IntegrityError as ex:
                if ex.args[0] == '23000':
                    logging.info(f"item already exists in db: order_key='{order_key}', item=({item.to_dict()})")
                    
            except Exception as other_ex:
                (exception_type, exception_value, exception_traceback) = sys.exc_info()
                logging.error(f"item insert failed: item=({item.to_dict()}), exception=({other_ex})")
        return

    def get_order_primary_key(self, bite_order_id: str, db_table_name:str = 'Orders') -> int:
        """
        Looks in the Orders table for an order with the matching Bite Order ID, then returns the orders' primary key

        :param bite_order_id: the Bite Order ID for the order that you with to find

        :return: order_pk: the primary key ID of the order in the Orders table that has the provided Bite Order ID
        """

        # logging.debug("in get_order_primary_key", {'bite_order_id': bite_order_id})

        with self.connection.cursor() as cursor:
            # retrieve the primary key ID of the order
            query= f"SELECT OrderID FROM dbo.{db_table_name} WHERE BiteOrderID = ?;"
            cursor_result = cursor.execute(query, bite_order_id)

            # make sure that we aren't getting more than 1 result
            # cursor_output = [dict(zip(zip(*cursor_result.description)[0], row)) for row in cursor_result.fetchall()]
            if cursor_result.arraysize > 1:
                raise Exception("got more than 1 row when attempting to retrieve an order's primary key")
            else:
                order_pk = cursor_result.fetchall()[0][0]

        logging.debug(f"primary key retrieved for order '{bite_order_id}': primary_key='{order_pk}'")
        return order_pk

    def update_timestamp(self, timestamp_id) -> None:
        """
        Overwrites the singular cell contained in the LastUpdatedTimestamp to reflect the last time that the fulfillment app was run

        :return: None
        """
        curr_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with self.connection.cursor() as cursor:
            # retrieve the primary key ID of the order
            cursor.execute("""UPDATE dbo.LastUpdatedTimestamp 
                                              SET LastUpdated = ? 
                                              WHERE ID = ?""", *(curr_timestamp, timestamp_id))
            logging.debug("LastUpdatedTimestamp timestamp was updated successfully")

        return