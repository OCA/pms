from odoo.tests.common import TransactionCase


class TestPmsFolioPrice(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_price_folio(self):
        """Test create reservation and services, and check price
        tax and discounts"""
