from odoo.exceptions import ValidationError

from .common import TestHotel


class TestPmsBoardServiceRoomType(TestHotel):
    def _create_common_scenario(self):
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
            {"name": "Room Type Class", "code_class": "SIN1"}
        )
        self.room_type = self.env["pms.room.type"].create(
            {
                "name": "Room Type",
                "code_type": "Type1",
                "class_id": self.room_type_class.id,
            }
        )

    def test_room_type_property_integrity(self):
        self._create_common_scenario()
        self.room_type.pms_property_ids = [self.property1.id]
        with self.assertRaises(ValidationError):
            self.board_service_room_type = self.env[
                "pms.board.service.room.type"
            ].create(
                {
                    "pms_board_service_id": self.board_service.id,
                    "pms_room_type_id": self.room_type.id,
                    "price_type": "fixed",
                    "pms_property_ids": self.property2,
                }
            )

    def test_pricelist_property_integrity(self):
        self._create_common_scenario()
        self.pricelist = self.env["product.pricelist"].create(
            {"name": "pricelist_1", "pms_property_ids": [self.property1.id]}
        )
        with self.assertRaises(ValidationError):
            self.env["pms.board.service.room.type"].create(
                {
                    "pms_board_service_id": self.board_service.id,
                    "pms_room_type_id": self.room_type.id,
                    "price_type": "fixed",
                    "pricelist_id": self.pricelist.id,
                    "pms_property_ids": self.property2,
                }
            )
