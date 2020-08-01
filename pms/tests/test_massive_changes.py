from odoo import fields
from odoo.exceptions import ValidationError

from .common import TestHotel


class TestMassiveChanges(TestHotel):

    # be aware using self.env.user.hotel_id because it is the value configure for the user running the tests

    # base massive change record
    def base_massive_change_vals(self, hotel_id=None):
        return {
            "hotel_id": hotel_id and hotel_id.id or self.main_hotel_property.id,
            "date_start": fields.Date.today(),
            "date_end": fields.Date.today(),
        }

    def pricelist_massive_change_vals(self, pricelist_id=None):
        return {
            "pricelist_id": pricelist_id and pricelist_id.id or self.list0.id,
            "price": 50.0,
        }

    def test_daily_pricelist(self):
        # Only daily pricelist can be manage by a massive change
        self.list0.pricelist_type = ""
        with self.assertRaises(ValidationError):
            vals = self.base_massive_change_vals()
            vals.update(self.pricelist_massive_change_vals())
            self.env["hotel.wizard.massive.changes"].create(vals)

        # create a valid record using a daily pricelist
        self.list0.pricelist_type = "daily"
        test_result = self.env["hotel.wizard.massive.changes"].create(vals)
        self.assertEqual(test_result.pricelist_id, self.list0)

    def test_pricelist_by_hotel(self):
        # Ensure the pricelist plan belongs to the current hotel #1
        with self.assertRaises(ValidationError):
            vals = self.base_massive_change_vals(self.demo_hotel_property)
            vals.update(self.pricelist_massive_change_vals())
            self.env["hotel.wizard.massive.changes"].create(vals)

        # Ensure the pricelist plan belongs to the current hotel #2
        with self.assertRaises(ValidationError):
            vals = self.base_massive_change_vals()
            vals.update(self.pricelist_massive_change_vals(self.list1))
            self.list1.hotel_ids = self.demo_hotel_property
            self.list1.pricelist_type = "daily"
            self.env["hotel.wizard.massive.changes"].create(vals)

        # create a valid record using the current hotel
        vals = self.base_massive_change_vals()
        vals.update(self.pricelist_massive_change_vals(self.list1))
        self.list1.hotel_ids = self.main_hotel_property
        self.list1.pricelist_type = "daily"
        test_result = self.env["hotel.wizard.massive.changes"].create(vals)
        self.assertEqual(test_result.pricelist_id.hotel_ids, self.main_hotel_property)

    def test_do_massive_change(self):
        # check the result of a massive change
        pass
