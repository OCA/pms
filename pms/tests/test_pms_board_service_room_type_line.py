from odoo.exceptions import ValidationError

from .common import TestHotel


class TestPmsBoardServiceRoomTypeLine(TestHotel):
    def test_check_product_property_integrity(self):
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
        self.board_service = self.env["pms.board.service"].create(
            {"name": "Board Service", "price_type": "fixed"}
        )
        self.room_type_class = self.env["pms.room.type.class"].create(
            {
                "name": "Room Type Class",
                "pms_property_ids": self.property1,
                "code_class": "SIN1",
            }
        )
        self.room_type = self.env["pms.room.type"].create(
            {
                "name": "Room Type",
                "code_type": "Type1",
                "class_id": self.room_type_class.id,
            }
        )
        self.board_service_room_type = self.env["pms.board.service.room.type"].create(
            {
                "pms_board_service_id": self.board_service.id,
                "pms_room_type_id": self.room_type.id,
                "price_type": "fixed",
                "pms_property_ids": self.property1,
            }
        )

        self.product = self.env["product.product"].create(
            {"name": "Product", "pms_property_ids": self.property2}
        )

        with self.assertRaises(ValidationError):
            self.env["pms.board.service.room.type.line"].create(
                {
                    "pms_board_service_room_type_id": self.board_service_room_type.id,
                    "product_id": self.product.id,
                }
            )
