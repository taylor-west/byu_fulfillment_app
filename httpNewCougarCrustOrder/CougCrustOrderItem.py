from .._CustomClasses.BiteOrder import *
from .._CustomClasses.BiteOrderItem import *

class CougCrustOrderItem(BiteOrderItem):
    def __init__(self, name, mod_string: str, note: str = None, quantity: int = 1, is_pizza: bool = False, pizza_num = None):
        BiteOrderItem.__init__(self, name, mod_string, note, quantity)

        self.is_pizza = is_pizza            # whether or no an item is a pizza
        self.pizza_num = pizza_num          # for pizzas, the number of the pizza within the order
        

        


