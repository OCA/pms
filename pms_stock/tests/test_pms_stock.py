# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class TestPmsStock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.location = cls.env["stock.location"].create(
            {"name": "Test Location", "usage": "internal"}
        )
        cls.property = cls.env["pms.property"].create(
            {"name": "Test Property", "stock_location_id": cls.location.id}
        )

    def test_property_stock_location(self):
        self.assertEqual(self.property.stock_location_id, self.location)

    def test_property_without_location(self):
        prop = self.env["pms.property"].create({"name": "No Location"})
        self.assertFalse(prop.stock_location_id)
