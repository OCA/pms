from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
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

    def test_display_name_room(self):
        """
        Check that the display_name field of a room is as expected.
        ------------
        A room is created and then it is checked that the display name
        field of this is composed of:
        room.name [room_type.default_code]
        """
        self.room1 = self.env["pms.room"].create(
            {
                "name": "Room 101",
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type1.id,
            }
        )
        expected_display_name = "%s [%s]" % (
            self.room1.name,
            self.room_type1.default_code,
        )
        self.assertEqual(
            self.room1.display_name,
            expected_display_name,
            "The display name of the room is not as expected",
        )

    def test_display_name_room_with_amenity(self):
        """
        Check that the display_name field of a room with one amenity
        is as expected.
        ------------
        A amenity is created with default code and with is_add_code_room_name
        field as True. A room is created in which the amenity created before
        is added in the room_amenity_ids field and then it is verified that
        the display name field of this is composed of:
        room.name [room_type.default_code] amenity.default_code
        """
        self.amenity_type1 = self.env["pms.amenity.type"].create(
            {
                "name": "Amenity Type 1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
            }
        )
        self.amenity1 = self.env["pms.amenity"].create(
            {
                "name": "Amenity 1",
                "pms_amenity_type_id": self.amenity_type1.id,
                "default_code": "A1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
                "is_add_code_room_name": True,
            }
        )
        self.room1 = self.env["pms.room"].create(
            {
                "name": "Room 101",
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type1.id,
                "room_amenity_ids": [(6, 0, [self.amenity1.id])],
            }
        )
        expected_display_name = "%s [%s] %s" % (
            self.room1.name,
            self.room_type1.default_code,
            self.amenity1.default_code,
        )
        self.assertEqual(
            self.room1.display_name,
            expected_display_name,
            "The display name of the room is not as expected",
        )

    def test_display_name_room_with_several_amenities(self):
        """
        Check that the display_name field of a room with several amenities
        is as expected.
        ------------
        Two amenities are created with diferent default code and with is_add_code_room_name
        field as True. A room is created in which the amenities created before are added in
        the room_amenity_ids field and then it is verified that the display name field of this
        is composed of:
        room.name [room_type.default_code] amenity1.default_code amenity2.default_code
        """
        self.amenity_type1 = self.env["pms.amenity.type"].create(
            {
                "name": "Amenity Type 1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
            }
        )
        self.amenity1 = self.env["pms.amenity"].create(
            {
                "name": "Amenity 1",
                "pms_amenity_type_id": self.amenity_type1.id,
                "default_code": "A1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
                "is_add_code_room_name": True,
            }
        )
        self.amenity2 = self.env["pms.amenity"].create(
            {
                "name": "Amenity 2",
                "pms_amenity_type_id": self.amenity_type1.id,
                "default_code": "B1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
                "is_add_code_room_name": True,
            }
        )
        self.room1 = self.env["pms.room"].create(
            {
                "name": "Room 101",
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type1.id,
                "room_amenity_ids": [(6, 0, [self.amenity1.id, self.amenity2.id])],
            }
        )
        expected_display_name = "%s [%s] %s %s" % (
            self.room1.name,
            self.room_type1.default_code,
            self.amenity1.default_code,
            self.amenity2.default_code,
        )
        self.assertEqual(
            self.room1.display_name,
            expected_display_name,
            "The display name of the room is not as expected",
        )

    def test_short_name_room_name_gt_4(self):
        """
        It checks through subtest that the short names of the
        rooms are correctly established when the names of these
        exceed 4 characters.
        -------------------------------------------------------
        First a room_type (Sweet Imperial) is created. Then 6 rooms
        are created with the name Sweet Imperial + room number. Finally
        in a loop we check that the short name of the rooms was set
        correctly: 'SW01, SW02, SW03...'
        """
        self.room_type2 = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Sweet Imperial",
                "default_code": "SWI",
                "class_id": self.room_type_class1.id,
                "list_price": 100,
            }
        )
        rooms = []
        self.room1 = self.env["pms.room"].create(
            {
                "name": "Sweet Imperial 101",
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type2.id,
            }
        )
        rooms.append(self.room1)
        self.room2 = self.env["pms.room"].create(
            {
                "name": "Sweet Imperial 102",
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type2.id,
            }
        )
        rooms.append(self.room2)
        self.room3 = self.env["pms.room"].create(
            {
                "name": "Sweet Imperial 103",
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type2.id,
            }
        )
        rooms.append(self.room3)
        self.room4 = self.env["pms.room"].create(
            {
                "name": "Sweet Imperial 104",
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type2.id,
            }
        )
        rooms.append(self.room4)
        self.room5 = self.env["pms.room"].create(
            {
                "name": "Sweet Imperial 105",
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type2.id,
            }
        )
        rooms.append(self.room5)
        self.room6 = self.env["pms.room"].create(
            {
                "name": "Sweet Imperial 106",
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type2.id,
            }
        )
        rooms.append(self.room6)
        for index, room in enumerate(rooms, start=1):
            with self.subTest(room):
                self.assertEqual(
                    room.short_name,
                    "SW0" + str(index),
                    "The short name of the room should be SW0" + str(index),
                )

    def test_short_name_room_name_lt_4(self):
        """
        Checks that the short name of a room is equal to the name
        when it does not exceed 4 characters.
        ---------------------------------------------------------
        A room is created with a name less than 4 characters (101).
        Then it is verified that the short name and the name of the
        room are the same.
        """
        self.room1 = self.env["pms.room"].create(
            {
                "name": "101",
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type1.id,
            }
        )
        self.assertEqual(
            self.room1.short_name,
            self.room1.name,
            "The short name of the room should be equal to the name of the room",
        )

    def test_short_name_gt_4_constraint(self):
        """
        Check that the short name of a room cannot exceed 4 characters.
        --------------------------------------------------------------
        A room named 201 is created. Afterwards, it is verified that a
        ValidationError is thrown when trying to change the short name
        of that room to 'SIN-201'.
        """
        self.room1 = self.env["pms.room"].create(
            {
                "name": "201",
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type1.id,
            }
        )

        with self.assertRaises(
            ValidationError,
            msg="The short_name of the room should not be able to be write.",
        ):
            self.room1.write({"short_name": "SIN-201"})
