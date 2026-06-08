# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class TestPmsWebsite(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.property = cls.env["pms.property"].create({"name": "Test Property"})

    def test_property_website_fields(self):
        self.assertTrue(hasattr(self.property, "website_id"))

    def test_property_cancelation_policy(self):
        self.assertFalse(self.property.cancelation_policy)
