from psycopg2 import IntegrityError

from odoo.exceptions import UserError
from odoo.tools import mute_logger

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
        with self.assertRaises(UserError, msg="Room has been created and it should't"):
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
        with self.assertRaises(UserError, msg="Room has been created and it should't"):
            self.env["pms.room"].create(
                {
                    "name": "Room 101",
                    "pms_property_id": self.pms_property3.id,
                    "room_type_id": self.room_type1.id,
                }
            )

    @mute_logger("odoo.sql_db")
    def test_name_property_unique_01(self):
        """
        PRE:    - room1 'Room 101' exists
                - room1 has pms_property1
        ACT:    - create a new room2
                - room2 has name 'Room 101'
                - room2 has pms_property1
        POST:   - Integrity error: already exists another room
                  with the same name on the same property
                - room2 not created
        """
        # ARRANGE
        self.env["pms.room"].create(
            {
                "name": "Room 101",
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type1.id,
            }
        )
        # ACT & ASSERT
        with self.assertRaises(
            IntegrityError, msg="Room has been created and it shouldn't"
        ):
            self.env["pms.room"].create(
                {
                    "name": "Room 101",
                    "pms_property_id": self.pms_property1.id,
                    "room_type_id": self.room_type1.id,
                }
            )

    def test_name_property_unique_02(self):
        """
        PRE:    - room1 'Room 101' exists
                - room1 has pms_property1
        ACT:    - create a new room2
                - room2 has name 'Room 101'
                - room2 has pms_property2
        POST:   - room2 created
        """
        # ARRANGE
        self.env["pms.room"].create(
            {
                "name": "Room 101",
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type1.id,
            }
        )
        # ACT & ASSERT
        try:
            self.env["pms.room"].create(
                {
                    "name": "Room 101",
                    "pms_property_id": self.pms_property2.id,
                    "room_type_id": self.room_type1.id,
                }
            )
        except IntegrityError:
            self.fail("Duplicated Room found but it shouldn't")
