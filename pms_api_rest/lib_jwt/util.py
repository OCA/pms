import logging
import os
import random
import string

from dateutil.parser import parse

_logger = logging.getLogger(__name__)


class Util:
    addons_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))

    def __init__(self):
        self.addons_path = self.addons_path.replace("jwt_provider", "")

    def generate_verification_code(self, length=8):
        return "".join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(length)
        )

    def toDate(self, pgTimeStr):
        return parse(pgTimeStr)

    def path(self, *paths):
        """Make a path"""
        return os.path.join(self.addons_path, *paths)

    def add_branch(self, tree, vector, value):
        """
        Given a dict, a vector, and a value, insert the value into the dict
        at the tree leaf specified by the vector.  Recursive!

        Params:
            data (dict): The data structure to insert the vector into.
            vector (list): A list of values representing the path to the leaf node.
            value (object): The object to be inserted at the leaf

        Example 1:
        tree = {'a': 'apple'}
        vector = ['b', 'c', 'd']
        value = 'dog'

        tree = add_branch(tree, vector, value)

        Returns:
            tree = { 'a': 'apple', 'b': { 'c': {'d': 'dog'}}}

        Example 2:
        vector2 = ['b', 'c', 'e']
        value2 = 'egg'

        tree = add_branch(tree, vector2, value2)

        Returns:
            tree = { 'a': 'apple', 'b': { 'c': {'d': 'dog', 'e': 'egg'}}}

        Returns:
            dict: The dict with the value placed at the path specified.

        Algorithm:
            If we're at the leaf, add it as key/value to the tree
            Else: If the subtree doesn't exist, create it.
                Recurse with the subtree and the left shifted vector.
            Return the tree.

        """
        key = vector[0]
        tree[key] = (
            value
            if len(vector) == 1
            else self.add_branch(tree[key] if key in tree else {}, vector[1:], value)
        )
        return tree

    def create_dict(self, d):
        res = {}
        for k, v in d.items():
            ar = k.split(".")
            filter(None, ar)
            self.add_branch(res, ar, v)
        return res


util = Util()
