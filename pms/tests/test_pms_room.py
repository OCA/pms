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

    def test_inconsistency_room_ubication_property(self):
        """
        Room property and its ubication properties are inconsistent.
        A Room with property that is not included in available properties
        for its ubication cannot be created.
        """
        # ARRANGE
        ubication1 = self.env["pms.ubication"].create(
            {
                "name": "UbicationTest",
                "pms_property_ids": [
                    (4, self.pms_property1.id),
                ],
            }
        )
        # ACT & ASSERT
        with self.assertRaises(
            UserError,
            msg="The room should not be created if its property is not included "
            "in the available properties for its ubication.",
        ):
            self.env["pms.room"].create(
                {
                    "name": "Room 101",
                    "pms_property_id": self.pms_property2.id,
                    "room_type_id": self.room_type1.id,
                    "ubication_id": ubication1.id,
                }
            )

    def test_consistency_room_ubication_property(self):
        """
        Room property and its ubication properties are consistent.
        A Room with property included in available properties
        for its ubication can be created.
        """
        # ARRANGE
        ubication1 = self.env["pms.ubication"].create(
            {
                "name": "UbicationTest",
                "pms_property_ids": [
                    (4, self.pms_property1.id),
                ],
            }
        )
        # ACT
        new_room1 = self.env["pms.room"].create(
            {
                "name": "Room 101",
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type1.id,
                "ubication_id": ubication1.id,
            }
        )
        # ASSERT
        self.assertIn(
            new_room1.pms_property_id,
            ubication1.pms_property_ids,
            "The room should be created if its property belongs to the availabe"
            "properties for its ubication.",
        )

    def test_inconsistency_room_type_property(self):
        """
        Room property and its room type properties are inconsistent.
        A Room with property that is not included in available properties
        for its room type cannot be created.
        """
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
            UserError,
            msg="The room should not be created if its property is not included "
            "in the available properties for its room type.",
        ):
            self.env["pms.room"].create(
                {
                    "name": "Room 101",
                    "pms_property_id": self.pms_property3.id,
                    "room_type_id": self.room_type1.id,
                }
            )

    def test_consistency_room_type_property(self):
        """
        Room property and its room type properties are inconsistent.
        A Room with property included in available properties
        for its room type can be created.
        """
        # ARRANGE & ACT
        room1 = self.env["pms.room"].create(
            {
                "name": "Room 101",
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type1.id,
            }
        )
        # ASSERT
        self.assertIn(
            room1.pms_property_id,
            self.room_type1.pms_property_ids,
            "The room should be created if its property is included "
            "in the available properties for its room type.",
        )

    @mute_logger("odoo.sql_db")
    def test_room_name_uniqueness_by_property(self):
        """
        Check that there are no two rooms with the same name in the same property
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
            IntegrityError,
            msg="The room should not be created if its name is equal "
            "to another room that belongs to the same property.",
        ):
            self.env["pms.room"].create(
                {
                    "name": "Room 101",
                    "pms_property_id": self.pms_property1.id,
                    "room_type_id": self.room_type1.id,
                }
            )

    def test_room_name_duplicated_different_property(self):
        """
        Check that two rooms with the same name can exist in multiple properties
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
            self.fail(
                "The room should be created even if its name is equal "
                "to another room, but that room not belongs to the same property."
            )
