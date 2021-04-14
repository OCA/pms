from odoo.exceptions import ValidationError

from .common import TestPms


class TestPmsRoom(TestPms):
    def setUp(self):
        super().setUp()
        self.pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property_2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )

        self.room_type1 = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id, self.pms_property2.id],
                "name": "Single",
                "default_code": "SIN",
                "class_id": self.room_type_class1.id,
                "list_price": 30,
            }
        )

    def test_check_property_ubication(self):
        # ARRANGE
        ubication1 = self.env["pms.ubication"].create(
            {
                "name": "UbicationTest",
                "pms_property_ids": [
                    (4, self.pms_property1.id),
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
                    "pms_property_id": self.pms_property2.id,
                    "room_type_id": self.room_type1.id,
                    "ubication_id": ubication1.id,
                }
            )

    def test_check_property_room_type(self):
        # ARRANGE
        self.pms_property3 = self.env["pms.property"].create(
            {
                "name": "Property_3",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        # ACT & ARRANGE
        with self.assertRaises(
            ValidationError, msg="Room has been created and it should't"
        ):
            self.env["pms.room"].create(
                {
                    "name": "Room 101",
                    "pms_property_id": self.pms_property3.id,
                    "room_type_id": self.room_type1.id,
                }
            )
