import logging
from .._HelperFunctions.parse_data_helpers import *
from .._Reference.bite_info import *
from .BiteOrderItem import *


# function to help in cleaning the data
def format_order_val(param_name: str, param_val, expected_type: type, is_nullable: bool = False):
    """
    A function that cleans up raw data into the appropriate format for database entry

    :param param_name: the name of the parameter that is being cleaned (used to identify guest_phone for special formatting)
    :param param_val: the current value of the parameter
    :param expected_type: the type that the parameter should be
    :param is_nullable: whether it is acceptable for the parameter to be null
    :return: param_val: the cleaned and formatted param_val
    """

    # checks if it is ok for this param_val to be null
    if param_val is None and is_nullable:
        return
    # makes sure that the param_val exists if it is supposed to
    elif (param_val is None) and (not is_nullable):
        raise ValueError(f"error while prepping param {param_name} for order: param is NoneType but is not nullable")
    # special case for phone numbers
    elif param_name == "guest_phone":
        if isinstance(param_val, (float, int)):
            # convert the phone number from float or int to a string
            return f"{param_name:.0f}"
        elif isinstance(param_val, (str)):
            return param_val
        else:
            raise ValueError(
                f"error while prepping param {param_name}: expected {expected_type}, got {type(param_val)}. (value = {param_val})")
    # special case for datetime (should output a string formatted 'YYYY-MM-DD hh:mm:ss')
    elif expected_type == datetime:
        if isinstance(param_val, str):
            return isoparse(param_val).astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')           # convert to UTC
        elif isinstance(param_val, datetime):
            return param_val.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')      
        else:
            raise ValueError(
                f"error while prepping param {param_name}: expected {expected_type}, got {type(param_val)}. (value = {param_val})")
    # checks for ints
    elif expected_type == int:
        if isinstance(param_val, int):
            return param_val
        else:
            return int(param_val)
    # checks for strings
    elif expected_type == str:
        if isinstance(param_val, str):
            return param_val
        else:
            return str(param_val)
    # we shouldn't really have to use any types other than datetime, string, and int
    else:
        raise ValueError(
            f"error while prepping param {param_name}: expected {expected_type}, got {type(param_val)}. (value = {param_val})")



##############################
##   Class to store Orders  ##
class BiteOrder:
    def __init__(self, bite_order_id, order_num, origin_site, created_date, ready_date, dining_option, guest_email,
                 guest_id, guest_phone, outpost_location, delivery_address, is_cancelled,
                 order_items_array, order_note):

        self.bite_order_id = bite_order_id
        self.orderNum = order_num
        self.created_date = created_date
        self.origin_site = origin_site
        self.origin_site_id = None
        self.guest_id = guest_id
        self.guest_email = guest_email
        self.guest_phone = guest_phone
        self.outpost_location = outpost_location
        self.outpost_location_id = None
        self.delivery_address = delivery_address
        self.ready_date = ready_date
        self.dining_option = dining_option
        self.dining_option_id = None
        self.order_note = order_note
        self.is_cancelled = is_cancelled
        self.fulfillment_status_id = None

        # self.items is a list of OrderItems that are associated with this order
        self.items = []  # a list of items that are associated with this order
        if len(order_items_array) > 0:
            # if raw json objects were passed in
            if type(order_items_array[0]) is dict:
                for curr_item in order_items_array:
                    self.add_item(curr_item)

            # if an array of already constructed OrderItem objects was passed in
            elif issubclass(type(order_items_array[0]), BiteOrderItem):
                self.items = order_items_array

            else:
                raise TypeError('order_items_array expected to have items of type dict or of parent class BiteOrder.'  +
                                f'Instead found items of type {type(order_items_array[0]).__qualname__}')


        # cleans and formats the order parameters taken from the json data
        self.clean_order_values()
    
        return


    def clean_order_values(self) -> None:
        """
        makes sure that the order information has the correct data type and is in the correct format,
        and adds foreign key id numbers to the appropriate fields (origin_site_id, outpost_location_id,
        dining_option_id, and fulfillment_status_id)
        :return: None
        """

        # calls either prep_param or generates a value for the special case

        self.bite_order_id = format_order_val("bite_order_id", self.bite_order_id, expected_type=str)  # varchar in DB

        self.orderNum = format_order_val("orderNum", self.orderNum, expected_type=str)  # varchar in DB

        self.created_date = format_order_val("created_date", self.created_date,
                                             expected_type=datetime)  # datetime in DB (need to input as string formatted "YYYY-MM-DD hh:mm:ss")

        self.origin_site = format_order_val("origin_site", self.origin_site, expected_type=str)  # not in DB

        # looks up the index of the fulfillment site in the DB using the KEYS dictionary (from reference.db_inf.py)
        logging.debug(f"getting FK for FulfillmentSites: search={self.origin_site}")
        self.origin_site_id = KEYS["FulfillmentSites"][self.origin_site]  # FK int in DB

        self.guest_id = format_order_val("guest_id", self.guest_id, expected_type=str)  # varchar in DB

        self.guest_email = format_order_val("guest_email", self.guest_email, expected_type=str)  # varchar in DB

        self.guest_phone = format_order_val("guest_phone", self.guest_phone,
                                            expected_type=(int, float, str),
                                            is_nullable=True)  # varchar in DB (NULLABLE)

        # looks up the index of the outpost in the DB using the KEYS dictionary (from reference.db_inf.py)
        self.outpost_location = format_order_val("outpost_location", self.outpost_location,
                                                 expected_type=str, is_nullable=True)  # not in DB
        if self.outpost_location is not None:
            logging.debug("getting FK for OutpostLocations: search={self.outpost_location}")
            self.outpost_location_id = KEYS["OutpostLocations"][self.outpost_location]  # FK int in DB (NULLABLE)

        self.delivery_address = format_order_val("delivery_address", self.delivery_address,
                                                 expected_type=str, is_nullable=True)  # text in DB (NULLABLE)

        self.ready_date = format_order_val("ready_date", self.ready_date, expected_type=datetime)   # datetime in DB (need to input as string formatted "YYYY-MM-DD hh:mm:ss")


        # looks up the index of the dining option in the DB using the KEYS dictionary (from reference.db_inf.py)
        # we already made sure that the diningOption was in the list of dining options that we can convert from (did this in parse_reports_into_orders)
        cleaned_dining_option = format_order_val("dining_option", self.dining_option, expected_type=str)  # not in DB
        self.dining_option_id = KEYS["DiningOptions"][self.dining_option]  # FK int in DB
        self.dining_option = DINING_OPTION_CONVERSIONS[cleaned_dining_option]
        logging.debug(f"getting FK for DiningOption: search={self.dining_option}")
        


        self.order_note = format_order_val("order_note", self.order_note,
                                           expected_type=str, is_nullable=True)  # text in DB (NULLABLE)

        # Converts the is_cancelled boolean value found in the order json into the foreign key
        # value for either a 'Cancelled' (9) or 'New' (1) order
        logging.debug(f"getting FK for FulfillmentStatuses: search={['Cancelled' if self.is_cancelled else 'New']}")
        self.fulfillment_status_id = KEYS["FulfillmentStatuses"]["Cancelled"] if self.is_cancelled else \
            KEYS["FulfillmentStatuses"]["New"]  # FK int in DB

        return

    def add_item(self, item_dict: dict) -> None:
        """
        adds an OrderItem object to the order.items dictionary, or increments quantity on existing OrderItem

        :param item_dict: a dictionary defining the elements of the order, as found in the Bite 'Reporting' API JSON response

        :return: None
        """

        # generates a mod_string for the current item
        curr_item_mod_string = make_mod_string(item_dict)

        # gets a list of items already stored with the same name and mod_string str_value
        matching_items = [stored_item for stored_item in self.items
                          if (stored_item.name == item_dict["name"])
                          and (stored_item.mod_string == curr_item_mod_string)]

        # checks if there are any matching items already stored
        if len(matching_items) == 0:
            # item has no duplicates --> add item to the self.items list

            # check for a note
            if "note" in item_dict.keys():
                order_note = item_dict["note"]
            else:
                order_note = None

            # creates a new OrderItem object with quantity 1
            curr_item_obj = BiteOrderItem(name=item_dict["name"],
                                      mod_string=curr_item_mod_string,
                                      note=order_note,
                                      quantity=1)

            self.items.append(curr_item_obj)
            logging.debug(f"item added: {curr_item_obj.to_dict()}")
        elif len(matching_items) == 1:
            # item has a single duplicate --> increment quantity on existing item
            matching_item = matching_items[0]
            matching_item.quantity += 1
            logging.debug(f"item already exists, incremented quantity: {matching_item.to_dict()}")
        else:
            # there was more than one duplicate found. This should not happen.
            logging.error(f"too many duplicates found while adding item: item_bite_order_id='{self.bite_order_id}', num_duplicates={len(matching_items)}, duplicate_name='{item_dict['name']}', duplicate_mod_string='{curr_item_mod_string}'")

        return

    def to_dict(self, include_items: bool = False) -> dict:
        order_dict = {'bite_order_id': self.bite_order_id,
                      'orderNum': self.orderNum,
                      'created_date': self.created_date,
                      'origin_site': self.origin_site,
                      'origin_site_id': self.origin_site_id,
                      'guest_id': self.guest_id,
                      'guest_email': self.guest_email,
                      'guest_phone': self.guest_phone,
                      'outpost_location': self.outpost_location,
                      'outpost_location_id': self.outpost_location_id,
                      'delivery_address': self.delivery_address,
                      'ready_date': self.ready_date,
                      'dining_option': self.dining_option,
                      'dining_option_id': self.dining_option_id,
                      'order_note': self.order_note,
                      'is_cancelled': self.is_cancelled,
                      'fulfillment_status_id': self.fulfillment_status_id}
        if include_items:
            order_dict.update({'items': self.items})

        return order_dict
