from odoo.exceptions import ValidationError
from odoo.tests import common, tagged


@tagged("standard", "nice")
class TestPmsPricelist(common.TransactionCase):
    def test_advanced_pricelist_exists(self):

        # ARRANGE
        key = "product.product_pricelist_setting"
        value = "advanced"

        # ACT
        found_value = self.env["ir.config_parameter"].sudo().get_param(key)

        # ASSERT
        self.assertEqual(found_value, value, "Parameter doesn't exist")

    def test_product_pricelist_setting_modified(self):

        # ARRANGE
        key = "product.product_pricelist_setting"
        value = "basic"

        # ACT & ASSERT
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env["ir.config_parameter"].set_param(key, value)

    def test_product_pricelist_setting_unlink(self):

        # ARRANGE
        key = "product.product_pricelist_setting"
        value = "advanced"

        # ACT & ASSERT
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env["ir.config_parameter"].search(
                [("key", "=", key), ("value", "=", value)]
            ).unlink()
