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
            {
                "name": "Board Service",
            }
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
