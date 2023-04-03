import datetime
from dateutil.parser import isoparse
import sys
import pyodbc
import logging

from .._CustomClasses.DatabaseObject import *
from .._CustomClasses import BiteOrder
from .._Reference.db_info import SERVER_NAME, DATABASE_NAME, DRIVER, DB_USERNAME, DB_PASSWORD, KEYS

from .CougCrustOrderItem import CougCrustOrderItem

COUG_CRUST_ORDERS_TABLE_NAME = 'CougarCrustOrders'
COUG_CRUST_ORDER_ITEMS_TABLE_NAME = 'CougarCrustOrderItems'


class CougCrustDBObject(DatabaseObject):
    def __init__(self) -> None:
        DatabaseObject.__init__(self)
        return

    def add_order(self, order: BiteOrder) -> bool:
        return DatabaseObject.add_order(self, order, db_table_name = COUG_CRUST_ORDERS_TABLE_NAME)

    def add_order_item(self, item: CougCrustOrderItem, order_key: int) -> None:
        # logging.debug(f"adding order item", {'order_key': order_key, 'item': item.to_dict()})

        value_fields = "(OrderID, " + \
                        "ItemName, " + \
                        "ModString, " + \
                        "Quantity, " + \
                        "IsPizza, " + \
                        "PizzaNumber, " + \
                        "SpecialNote)"

        item_values = (order_key,
                       item.name,
                       item.mod_string,
                       item.quantity,
                       item.is_pizza,
                       item.pizza_num,
                       item.note)

        with self.connection.cursor() as cursor:
            try:
                sql = f"""
                         INSERT INTO dbo.{COUG_CRUST_ORDER_ITEMS_TABLE_NAME} {value_fields} 
                         VALUES (?, ?, ?, ?, ?, ?, ?)
                       """.strip(" \n   ")
                cursor.execute(sql, item_values)
                logging.debug(f"item added (order_key={order_key}, item={item.to_dict()})")
            except pyodbc.IntegrityError as ex:
                if ex.args[0] == '23000':
                    logging.debug(f"item already exists (order_key={order_key}, item={item.to_dict()})")
            except Exception as other_ex:
                (exception_type, exception_value, exception_traceback) = sys.exc_info()
                logging.error(f"item insert failed: exception=({other_ex}), item=({item.to_dict()})")
        return


    # gets the Primary Key of an order in the CougarCrustOrders Table
    def get_order_primary_key(self, bite_order_id: str) -> int:
        return DatabaseObject.get_order_primary_key(self, bite_order_id, db_table_name=COUG_CRUST_ORDERS_TABLE_NAME)


    def get_pizza_pos_ids(self):
        with self.connection.cursor() as cursor:
            try:
                result = cursor.execute('SELECT POS_ID FROM CougarCrustPizzaPosIds')
            except Exception as ex:
                exception_type, exception_value, _ = sys.exc_info()
                logging.error(f"Failed to retrieve pizza pos_ids: exception=({ex})")
            
            pos_ids_array = [row_tuple[0] for row_tuple in result.fetchall()]
            return pos_ids_array


    def update_pizza_count(self, order_id, pizza_count) -> bool:
        successful = False
        try:
            with self.connection.cursor() as cursor:
                sql = f"""
                        UPDATE {COUG_CRUST_ORDERS_TABLE_NAME}
                        SET NumPizzas = {pizza_count}
                        WHERE OrderID = {order_id}
                       """.strip(" \n  ")
                cursor.execute(sql)
                successful = True

        except Exception as ex:
            exception_type, exception_value, _ = sys.exc_info()
            logging.error(f"Failed to retrieve pizza pos_ids: expception=({ex})")
            
        return successful
