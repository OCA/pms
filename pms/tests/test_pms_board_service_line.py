from odoo.exceptions import ValidationError

from .common import TestHotel


class TestPmsBoardService(TestHotel):
    def test_property_integrity(self):
        self.company1 = self.env["res.company"].create(
            {
                "name": "Pms_Company_Test",
            }
        )
        self.property1 = self.env["pms.property"].create(
            {
                "name": "Pms_property_test1",
                "company_id": self.company1.id,
                "default_pricelist_id": self.env.ref("product.list0").id,
            }
        )
        self.property2 = self.env["pms.property"].create(
            {
                "name": "Pms_property_test2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.env.ref("product.list0").id,
            }
        )
        self.product = self.env["product.product"].create(
            {"name": "Product", "pms_property_ids": self.property1}
        )

        self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Board Service",
                "price_type": "fixed",
            }
        )
        with self.assertRaises(ValidationError):
            board_service_line = self.board_service_line = self.env[
                "pms.board.service.line"
            ].create(
                {
                    "product_id": self.product.id,
                    "pms_board_service_id": self.board_service.id,
                }
            )
            board_service_line.pms_property_ids = [self.property2.id]
