from odoo.tests.common import SavepointCase


class TestPmsFolioInvoice(SavepointCase):
    def setUp(self):
        super(TestPmsFolioInvoice, self).setUp()

    def test_price_reservation(self):
        """Test create a reservation, and check price and discounts"""

    def test_general_discount_reservation(self):
        """Test a discount in reservation head, and check lines"""
