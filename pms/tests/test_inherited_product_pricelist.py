from .common import TestHotel
from odoo import fields
from odoo.exceptions import ValidationError


class TestInheritedProductPricelist(TestHotel):

    # be aware using self.env.user.hotel_id because it is the value configure for the user running the tests

    def test_daily_pricelist(self):
        # A daily pricelist must be related with one and only one hotel #1
        with self.assertRaises(ValidationError):
            self.list0.hotel_ids += self.demo_hotel_property

        # A daily pricelist must be related with one and only one hotel #2
        with self.assertRaises(ValidationError):
            self.list0.hotel_ids = False

        # create a valid record using a daily pricelist
        test_result = self.env['product.pricelist'].create({
            'name': 'Test Daily Pricelist',
            'hotel_ids': [(4, self.demo_hotel_property.id)]
        })
        self.assertEqual(test_result.pricelist_type, 'daily')
        self.assertEqual(test_result.hotel_ids, self.demo_hotel_property)

    def test_pricelist_by_hotel(self):
        # Relationship mismatch when the pricelist is already used as default in a different hotel
        with self.assertRaises(ValidationError):
            self.list0.hotel_ids = self.demo_hotel_property
