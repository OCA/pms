from odoo.tests.common import SavepointCase


class TestPmsFolioInvoice(SavepointCase):
    def setUp(self):
        super(TestPmsFolioInvoice, self).setUp()

    def test_invoice_folio(self):
        """Test create and invoice from the Folio, and check qty invoice/to invoice,
        and the related amounts"""

    def test_invoice_by_days_folio(self):
        """Test create and invoice from the Folio, and check qty invoice/to invoice,
        and the related amounts in a specific segment of days (reservation lines)"""

    def test_invoice_by_services_folio(self):
        """Test create and invoice from the Folio, and check qty invoice/to invoice,
        and the related amounts in a specific segment of services (qtys)"""

    def test_invoice_board_service(self):
        """Test create and invoice from the Folio, and check qty invoice/to invoice,
        and the related amounts with board service linked"""

    def test_invoice_line_group_by_room_type_sections(self):
        """Test create and invoice from the Folio, and check qty invoice/to invoice,
        and the grouped invoice lines by room type, by one
        line by unit prices/qty with nights"""

    def test_autoinvoice_folio(self):
        """ Test create and invoice the cron by partner preconfig automation """

    def test_downpayment(self):
        """Test invoice qith a way of downpaument and check dowpayment's
        folio line is created and also check a total amount of invoice is
        equal to a respective folio's total amount"""

    def test_invoice_with_discount(self):
        """Test create with a discount and check discount applied
        on both Folio lines and an inovoice lines"""

    def test_reinvoice(self):
        """Test the compute reinvoice folio take into account
        nights and services qty invoiced"""
