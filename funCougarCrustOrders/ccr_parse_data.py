import sys

from dateutil.parser import isoparse
from datetime import *

from .._HelperFunctions import parse_data_helpers
from .._CustomClasses.BiteOrder import *
from .._CustomClasses import BiteOrderItem as ord_item
from .CougCrustOrderItem import *

INDENT_CHAR = f"{' ' * 3}"
DELIMIT_CHAR = '\n'


def ccr_parse_order_items(item_json_objs, pizza_pos_ids: list[str]):
    """
        Parses order items into cougar crust order items

        Params:
        --------------
        item_json_objs: list[dict] -> List of orderitem dictionaries
        pizza_pos_ids: list[str] -> List of posids for items that are pizzas

        Return -> list[CougarCrustOrderItem]
    """
    order_items = []
    pizza_count = 0

    for order_item in item_json_objs:
        modifier_str = ord_item.make_mod_string(order_item)
        special_note = order_item["note"] if "note" in order_item.keys() else ""
        pos_id = order_item["posId"]

        if pos_id in pizza_pos_ids:             # check if item is a pizza
            is_pizza = True           
            pizza_count += 1
            pizza_num = pizza_count
        else:
            is_pizza = False
            pizza_num = None

        coug_crust_order_item = CougCrustOrderItem(name = order_item["name"],
                                                   mod_string = modifier_str,
                                                   note = special_note,
                                                   quantity = 1,
                                                   is_pizza = is_pizza,
                                                   pizza_num = pizza_num
                                                   )
        order_items.append(coug_crust_order_item)

    return order_items


def ccr_parse_report_into_orders(report_dict: dict, pizza_pos_ids) -> list[BiteOrder]:
    ccr_order_item_func = lambda report: ccr_parse_order_items(report, pizza_pos_ids)
    return parse_data_helpers.parse_report_into_orders(report_dict, 
                                                       parse_order_item_func=ccr_order_item_func)
