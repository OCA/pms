from odoo.exceptions import ValidationError

from .common import TestPms


class TestPmsPricelistSettings(TestPms):
    def test_advanced_pricelist_exists(self):
        """
        Check if value of Pricelist parameter in sales settings is Advanced Price Rules.
        Find the value of Pricelist parameter
        with the key product.product_pricelist_setting and check if is equal to "advanced".
        """
        # ARRANGE
        key = "product.product_pricelist_setting"
        value = "advanced"

        # ACT
        found_value = self.env["ir.config_parameter"].sudo().get_param(key)

        # ASSERT
        self.assertEqual(
            found_value, value, "Parameter of Pricelist in setting is not 'advanced'"
        )

    def test_product_pricelist_setting_not_modified(self):
        """
        Check that Pricelist parameter 'advanced' cannot be modified.
        Set the value of product.product_pricelist_setting to 'basic'
        but is not possible because this only can be 'advanced'.
        """
        # ARRANGE
        key = "product.product_pricelist_setting"
        value = "basic"

        # ACT & ASSERT
        with self.assertRaises(
            ValidationError, msg="The Pricelist parameter 'advanced' was modified."
        ):
            self.env["ir.config_parameter"].set_param(key, value)

    def test_product_pricelist_setting_not_unlink(self):
        """
        Check that Pricelist parameter 'advanced' cannot be unlink.
        Try to unlink the parameter product_pricelist with value 'advanced'
        but this should be impossible.
        """
        # ARRANGE
        key = "product.product_pricelist_setting"
        value = "advanced"

        # ACT & ASSERT
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env["ir.config_parameter"].search(
                [("key", "=", key), ("value", "=", value)]
            ).unlink()
