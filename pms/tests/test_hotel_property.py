from odoo import fields
from odoo.exceptions import ValidationError

from .common import TestHotel


class TestHotelProperty(TestHotel):

    # be aware using self.env.user.hotel_id because it is the value configure for the user running the tests

    def test_default_pricelist(self):
        # A default pricelist must be related with one and only one hotel
        with self.assertRaises(ValidationError):
            self.demo_hotel_property.default_pricelist_id = self.list0
