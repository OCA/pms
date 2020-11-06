from odoo.tests import common, tagged


@tagged("standard", "nice")
class TestPmsPricelist(common.TransactionCase):
    def test_advanced_pricelist_exists(self):

        # ARRANGE
        key = "product.product_pricelist_setting"
        value = "Advance"

        # ACT
        found_value = self.env["ir.config_parameter"].sudo().get_param(key)

        # ASSERT
        self.assertEqual(found_value, value, "The register wasn't created")
