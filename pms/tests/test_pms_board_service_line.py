from odoo.exceptions import UserError

from .common import TestPms


class TestPmsBoardService(TestPms):
    def test_pms_bsl_product_property_integrity(self):
        """
        Creation of a board service line without property, of a product
        only available for a specific property.
        """
        # ARRANGE
        product = self.env["product.product"].create(
            {"name": "Product", "pms_property_ids": [self.pms_property1.id]}
        )
        board_service = self.env["pms.board.service"].create(
            {
                "name": "Board Service",
                "default_code": "CB",
            }
        )
        # ACT & ASSERT
        with self.assertRaises(
            UserError, msg="Board service line shouldnt be created."
        ):
            self.env["pms.board.service.line"].create(
                {
                    "product_id": product.id,
                    "pms_board_service_id": board_service.id,
                }
            )

    def test_pms_bsl_board_service_property_integrity(self):
        """
        Creation of a board service line without property, of board service
        only available for a specific property.
        """
        # ARRANGE
        pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 1",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        product = self.env["product.product"].create(
            {"name": "Product", "pms_property_ids": [self.pms_property1.id]}
        )

        board_service = self.env["pms.board.service"].create(
            {
                "name": "Board Service",
                "default_code": "CB",
                "pms_property_ids": [pms_property2.id],
            }
        )
        # ACT & ASSERT
        with self.assertRaises(
            UserError, msg="Board service line shouldnt be created."
        ):
            self.env["pms.board.service.line"].create(
                {
                    "product_id": product.id,
                    "pms_board_service_id": board_service.id,
                }
            )

    def test_pms_bsl_board_service_line_prop_integrity(self):
        """
        Creation of a board service line with a specific property,
        of board service without property.
        """
        # ARRANGE
        pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 1",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        product = self.env["product.product"].create(
            {"name": "Product", "pms_property_ids": [self.pms_property1.id]}
        )
        board_service = self.env["pms.board.service"].create(
            {
                "name": "Board Service",
                "default_code": "CB",
            }
        )
        # ACT & ASSERT
        with self.assertRaises(
            UserError, msg="Board service line shouldnt be created."
        ):
            self.env["pms.board.service.line"].create(
                {
                    "product_id": product.id,
                    "pms_board_service_id": board_service.id,
                    "pms_property_ids": [pms_property2.id],
                }
            )
