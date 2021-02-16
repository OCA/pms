from odoo.exceptions import ValidationError
from odoo.tests import common


class TestPmsRoom(common.TransactionCase):
    def create_common_scenario(self):
        self.property1 = self.env["pms.property"].create(
            {
                "name": "Property_1",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
            }
        )

        self.property2 = self.env["pms.property"].create(
            {
                "name": "Property_2",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
            }
        )
        self.property3 = self.env["pms.property"].create(
            {
                "name": "Property_3",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
            }
        )

        self.room_type_class = self.env["pms.room.type.class"].create(
            {"name": "Room Class", "code_class": "ROOM"}
        )

        self.room_type = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.property1.id, self.property2.id],
                "name": "Single",
                "code_type": "SIN",
                "class_id": self.room_type_class.id,
                "list_price": 30,
            }
        )

    def test_check_property_floor(self):
        # ARRANGE
        self.create_common_scenario()
        floor = self.env["pms.floor"].create(
            {
                "name": "Floor",
                "pms_property_ids": [
                    (4, self.property1.id),
                ],
            }
        )
        # ACT & ARRANGE
        with self.assertRaises(
            ValidationError, msg="Room has been created and it should't"
        ):
            self.env["pms.room"].create(
                {
                    "name": "Room 101",
                    "pms_property_id": self.property2.id,
                    "room_type_id": self.room_type.id,
                    "floor_id": floor.id,
                }
            )

    def test_check_property_room_type(self):
        # ARRANGE
        self.create_common_scenario()
        # ACT & ARRANGE
        with self.assertRaises(
            ValidationError, msg="Room has been created and it should't"
        ):
            self.env["pms.room"].create(
                {
                    "name": "Room 101",
                    "pms_property_id": self.property3.id,
                    "room_type_id": self.room_type.id,
                }
            )
