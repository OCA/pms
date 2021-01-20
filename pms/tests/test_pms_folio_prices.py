from odoo.tests.common import SavepointCase


class TestPmsFolioPrice(SavepointCase):
    def setUp(self):
        super(TestPmsFolioPrice, self).setUp()

    def test_price_folio(self):
        """Test create reservation and services, and check price
        tax and discounts"""
