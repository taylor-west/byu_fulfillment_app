import logging
from .._HelperFunctions.parse_data_helpers import *
from .BiteOrder import *


def mod_string_recursion_helper(curr_item: dict, curr_substring: str, indent_num: int, indent_char:str = f"{' ' * 3}") -> str:
    # makes sure that we are receiving the correct type of input
    if not isinstance(curr_item, dict):
        raise ValueError(f"invalid data format for curr_item ({type(curr_item)})")

    # checks if the current item stores its modifiers in "modGroups" or "mods"
    if "modGroups" in curr_item.keys():
        mod_title = "modGroups"
    elif "mods" in curr_item.keys():
        mod_title = "mods"
    else:
        # modifier children should always be found in one of those two groups
        raise ValueError("item has neither mods nor modGroups")

    # create the substring for the current item
    if len(curr_item[mod_title]) != 0:
        # curr_item has modifier children --> continue recursion

        # adds the name of the current item so that it sits above its modifier children
        curr_item_substring = f"{curr_substring}\n{indent_char * indent_num}- {curr_item['name']}"

        if len(curr_item[mod_title]) != 0:  # makes sure that there are children to add
            # add substrings for all children under the current item
            for mod in curr_item[mod_title]:
                # get substrings of children modifiers (recursive)
                child_substring = mod_string_recursion_helper(mod, curr_substring, (indent_num + 1))

                # add them to the current substring
                # you don't add the indents here because they were added in the leaf nodes
                curr_item_substring += f"\n{indent_char}{child_substring}"
    else:
        # the current item is a "leaf node" --> contains no modifiers.

        # overwrite item_substring to prevent copying the full mod_string path,
        # and return the substring for just this item to its parent (this means
        # that we add the indents, but not the delimiter/newline)
        curr_item_substring = f"{indent_char * indent_num}- {curr_item['name']}"

    return curr_item_substring


# modstring format should be: delimiter = newline, indent = 3 spaces, with a '- ' before each modifier
def make_mod_string(curr_item: dict, indent_char: str = f"{' ' * 3}") -> str:
    if not isinstance(curr_item, dict):
        raise ValueError(f"invalid data format for curr_item ({type(curr_item)})")

    # initialize the mod_string by adding the root node (top level item) to the string
    # mod_string = f"{curr_item['name']}"
    mod_string = ""
    indent_num = 0

    # checks if the current item stores its modifiers in "modGroups" or "mods"
    if "modGroups" in curr_item.keys():
        mod_title = "modGroups"
    elif "mods" in curr_item.keys():
        mod_title = "mods"
    else:
        # modifier children should always be found in one of those two groups
        raise ValueError("item has neither mods nor modGroups")

    # adds the substrings of all modifier children
    if len(curr_item[mod_title]) > 0:  # makes sure that there are children
        # top level item has modifier children --> generate substrings for each child

        for mod in curr_item[mod_title]:
            # generate the substring for the current modifier child
            child_substring = mod_string_recursion_helper(mod, '', indent_num, indent_char)

            # add the child modifier substring to the mod_string
            mod_string += f"{indent_char * indent_num}{child_substring}"

    # if the top level item has no modifier children, just return the name of the top level item
    return mod_string.strip()



###################################
## Generic Bite Order Item Class ##
class BiteOrderItem:

    def __init__(self, name, mod_string: str, note: str = None, quantity: int = 1):
        self.name = name
        self.mod_string = mod_string
        self.note = note
        self.quantity = quantity
        return

    def to_dict(self):
        return {'name': self.name, 'mod_string': self.mod_string, 'note': self.note}

    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, BiteOrderItem):
            return False
        return other.mod_string == self.mod_string and  \
               other.name == self.name and \
               other.note == self.note

