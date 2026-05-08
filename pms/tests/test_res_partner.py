from odoo.tests import common


class TestResPartnerGetVat(common.TransactionCase):
    def test_get_vat_returns_vat(self):
        partner = self.env["res.partner"].create(
            {"name": "Partner with VAT", "vat": "ESA12345674"}
        )
        self.assertEqual(partner.get_vat(), "ESA12345674")

    def test_get_vat_empty_when_no_vat(self):
        partner = self.env["res.partner"].create({"name": "Partner without VAT"})
        self.assertEqual(partner.get_vat(), "")
