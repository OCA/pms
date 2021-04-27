# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError, ValidationError

from .common import TestPms


class TestRoomType(TestPms):
    def setUp(self):
        super().setUp()
        self.pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        self.company2 = self.env["res.company"].create(
            {
                "name": "Company 2",
            }
        )

        self.pms_property3 = self.env["pms.property"].create(
            {
                "name": "Property 3",
                "company_id": self.company2.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )

    def test_internal_case_01(self):
        """
        PRE:    - room_type1 does not exists
        ACT:    - create a new room_type1 room
                - room_type1 has code c1
                - room_type1 has property pms_property1
                - pms_property1 has company company1
                - room_type1 has company company1
        POST:   - room_type1 created
        """
        # ARRANGE & ACT & ASSERT
        try:
            # room_type1
            self.env["pms.room.type"].create(
                {
                    "name": "Room type 1",
                    "default_code": "c1",
                    "pms_property_ids": [(6, 0, [self.pms_property1.id])],
                    "company_id": self.company1.id,
                    "class_id": self.room_type_class1.id,
                }
            )
        except ValidationError:
            self.fail("Room type not created when it should")

    def test_internal_case_02(self):
        """
        PRE:    - room_type1 does not exists
        ACT:    - create a new room_type1 room
                - room_type1 has code c1
                - room_type1 has property pms_property1
                - pms_property1 has company1
                - room_type1 has company2
        POST:   - Integrity error, pms_property1 has company1 and room type company2
                - room_type1 not created
        """
        # ARRANGE & ACT & ASSERT
        with self.assertRaises(
            UserError, msg="The room type has been created and it shouldn't"
        ):
            # room_type1
            self.env["pms.room.type"].create(
                {
                    "name": "Room type 1",
                    "default_code": "c1",
                    "pms_property_ids": [(6, 0, [self.pms_property1.id])],
                    "company_id": self.company2.id,
                    "class_id": self.room_type_class1.id,
                }
            )

    def test_internal_case_03(self):
        """
        PRE:    - room_type1 does not exists
        ACT:    - create a new room_type1 room
                - room_type1 has code c1
                - room_type1 has property pms_property1 and pms_property3
                - pms_property1 has company company1
                - pms_property3 has company2
                - room_type1 has company2
        POST:   - Integrity error, pms_property1 has company1 and room type company2
                - room_type1 not created
        """
        # ARRANGE & ACT & ASSERT
        with self.assertRaises(
            UserError, msg="The room type has been created and it shouldn't"
        ):
            # room_type1
            self.env["pms.room.type"].create(
                {
                    "name": "Room type 1",
                    "default_code": "c1",
                    "pms_property_ids": [
                        (6, 0, [self.pms_property1.id, self.pms_property3.id])
                    ],
                    "company_id": self.company2.id,
                    "class_id": self.room_type_class1.id,
                }
            )

    def test_internal_case_04(self):
        """
        PRE:    - room_type1 does not exists
        ACT:    - create a new room_type1 room
                - room_type1 has code c1
                - room_type1 has property pms_property1 and pms_property3
                - pms_property1 has company company1
                - pms_property3 has company2
                - room_type1 has no company
        POST:   - room_type1 created
        """
        # ARRANGE & ACT & ASSERT
        try:
            # room_type1
            self.env["pms.room.type"].create(
                {
                    "name": "Room type 1",
                    "default_code": "c1",
                    "pms_property_ids": [
                        (6, 0, [self.pms_property1.id, self.pms_property3.id])
                    ],
                    "company_id": False,
                    "class_id": self.room_type_class1.id,
                }
            )
        except ValidationError:
            self.fail("Room type not created when it should")

    # external integrity
    def test_external_case_01(self):
        """
        PRE:    - room type room_type1 exists
                - room_type1 has code c1
                - room_type1 has property pms_property1
                - pms_property1 has company company1
                - room_type1 has no company
        ACT:    - create a new room_type2 room
                - room_type2 has code c1
                - room_type2 has property pms_property1
                - pms_property1 has company company1
                - room_type2 has no company
        POST:   - Integrity error: the room type already exists
                - room_type2 not created
        """
        # ARRANGE
        # room_type1
        self.env["pms.room.type"].create(
            {
                "name": "Room type 1",
                "default_code": "c1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
                "company_id": False,
                "class_id": self.room_type_class1.id,
            }
        )

        # ACT & ASSERT
        with self.assertRaises(
            ValidationError, msg="The room type has been created and it shouldn't"
        ):
            # room_type2
            self.env["pms.room.type"].create(
                {
                    "name": "Room type 2",
                    "default_code": "c1",
                    "pms_property_ids": [(6, 0, [self.pms_property1.id])],
                    "company_id": False,
                    "class_id": self.room_type_class1.id,
                }
            )

    def test_external_case_02(self):
        """
        PRE:    - room type room_type1 exists
                - room_type1 has code c1
                - room_type1 has property pms_property1
                - pms_property1 has company company1
                - room_type1 has no company
        ACT:    - create a new room_type2 room
                - room_type2 has code c1
                - room_type2 has property pms_property1
                - pms_property1 has company company1
                - room_type2 has company company1
        POST:   - Integrity error: the room type already exists
                - room_type2 not created
        """
        # ARRANGE
        # room_type1
        self.env["pms.room.type"].create(
            {
                "name": "Room type 1",
                "default_code": "c1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
                "company_id": False,
                "class_id": self.room_type_class1.id,
            }
        )

        # ACT & ASSERT
        with self.assertRaises(
            ValidationError, msg="The room type has been created and it shouldn't"
        ):
            # room_type2
            self.env["pms.room.type"].create(
                {
                    "name": "Room type 2",
                    "default_code": "c1",
                    "pms_property_ids": [(6, 0, [self.pms_property1.id])],
                    "company_id": self.company1.id,
                    "class_id": self.room_type_class1.id,
                }
            )

    def test_external_case_03(self):
        """
        PRE:    - room type room_type1 exists
                - room_type1 has code c1
                - room_type1 has property pms_property1
                - pms_property1 has company company1
                - room_type1 has company company1
        ACT:    - create a new room_type2 room
                - room_type2 has code c1
                - room_type2 has property pms_property1, pms_property2, pms_property3
                - pms_property1, pms_property2 has company company1
                - pms_property3 has company2
                - room_type2 has no company
        POST:   - Integrity error: the room type already exists
                - room_type not created
        """
        # ARRANGE
        # room_type1
        self.env["pms.room.type"].create(
            {
                "name": "Room type 1",
                "default_code": "c1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
                "company_id": self.company1.id,
                "class_id": self.room_type_class1.id,
            }
        )

        # ACT & ASSERT
        with self.assertRaises(
            ValidationError, msg="The room type has been created and it shouldn't"
        ):
            # room_type2
            self.env["pms.room.type"].create(
                {
                    "name": "Room type 2",
                    "default_code": "c1",
                    "pms_property_ids": [
                        (
                            6,
                            0,
                            [
                                self.pms_property1.id,
                                self.pms_property2.id,
                                self.pms_property3.id,
                            ],
                        )
                    ],
                    "company_id": False,
                    "class_id": self.room_type_class1.id,
                }
            )

    def test_single_case_01(self):
        """
        PRE:    - room type room_type1 exists
                - room_type1 has code c1
                - room_type1 with 2 properties pms_property1 and pms_property2
                - pms_property1 and pms_property2 have the same company company1
                - room_type1 has no company
        ACT:    - search room type with code c1 and pms_property1
                - pms_property1 has company company1
        POST:   - only room_type1 room type found
        """
        # ARRANGE
        room_type1 = self.env["pms.room.type"].create(
            {
                "name": "Room type 1",
                "default_code": "c1",
                "pms_property_ids": [
                    (6, 0, [self.pms_property1.id, self.pms_property3.id])
                ],
                "company_id": False,
                "class_id": self.room_type_class1.id,
            }
        )

        # ACT
        room_types = self.env["pms.room.type"].get_room_types_by_property(
            self.pms_property1.id, "c1"
        )

        # ASSERT
        self.assertEqual(room_types.id, room_type1.id, "Expected room type not found")

    def test_single_case_02(self):
        """
        PRE:    - room type room_type1 exists
                - room_type1 has code c1
                - room_type1 with 2 properties pms_property1 and pms_property3
                - pms_property1 and pms_property2 have different companies
                - pms_property1 have company company1 and pms_property3 have company2
                - room_type1 has no company
        ACT:    - search room type with code c1 and property pms_property1
                - pms_property1 has company company1
        POST:   - only room_type1 room type found
        """
        # ARRANGE
        room_type1 = self.env["pms.room.type"].create(
            {
                "name": "Room type 1",
                "default_code": "c1",
                "pms_property_ids": [
                    (6, 0, [self.pms_property1.id, self.pms_property3.id])
                ],
                "company_id": False,
                "class_id": self.room_type_class1.id,
            }
        )

        # ACT
        room_types = self.env["pms.room.type"].get_room_types_by_property(
            self.pms_property1.id, "c1"
        )

        # ASSERT
        self.assertEqual(room_types.id, room_type1.id, "Expected room type not found")

    def test_single_case_03(self):
        """
        PRE:    - room type room_type1 exists
                - room_type1 has code c1
                - room_type1 with 2 properties pms_property1 and pms_property2
                - pms_property1 and pms_property2 have same company company1
                - room_type1 has no company
        ACT:    - search room type with code c1 and property pms_property3
                - pms_property3 have company2
        POST:   - no room type found
        """
        # ARRANGE
        # room_type1
        self.env["pms.room.type"].create(
            {
                "name": "Room type 1",
                "default_code": "c1",
                "pms_property_ids": [
                    (6, 0, [self.pms_property1.id, self.pms_property2.id])
                ],
                "company_id": False,
                "class_id": self.room_type_class1.id,
            }
        )

        # ACT
        room_types = self.env["pms.room.type"].get_room_types_by_property(
            self.pms_property3.id, "c1"
        )

        # ASSERT
        self.assertFalse(room_types, "Room type found but it should have not found any")

    def test_single_case_04(self):
        """
        PRE:    - room type r1 exists
                - room_type1 has code c1
                - room_type1 properties are null
                - room_type1 company is company1
        ACT:    - search room type with code c1 and pms_property1
                - pms_property1 have company company1
        POST:   - only rroom_type1 room type found
        """
        # ARRANGE
        room_type1 = self.env["pms.room.type"].create(
            {
                "name": "Room type 1",
                "default_code": "c1",
                "pms_property_ids": False,
                "company_id": self.company1.id,
                "class_id": self.room_type_class1.id,
            }
        )

        # ACT
        room_types = self.env["pms.room.type"].get_room_types_by_property(
            self.pms_property1.id, "c1"
        )

        # ASSERT
        self.assertEqual(room_types.id, room_type1.id, "Expected room type not found")

    def test_single_case_05(self):
        """
        PRE:    - room type room_type1 exists
                - room_type1 has code c1
                - room_type1 properties are null
                - room_type1 company is company1
        ACT:    - search room type with code c1 and pms_property3
                - pms_property3 have company2
        POST:   - no room type found
        """
        # ARRANGE
        # room_type1
        self.env["pms.room.type"].create(
            {
                "name": "Room type r1",
                "default_code": "c1",
                "pms_property_ids": False,
                "company_id": self.company1.id,
                "class_id": self.room_type_class1.id,
            }
        )

        # ACT
        room_types = self.env["pms.room.type"].get_room_types_by_property(
            self.pms_property3.id, "c1"
        )

        # ASSERT
        self.assertFalse(room_types, "Room type found but it should have not found any")

    # tests with more than one room type
    def test_multiple_case_01(self):
        """
        PRE:    - room type room_type1 exists
                - room_type1 has code c1
                - room_type1 with 2 properties pms_property1 and pms_property2
                - pms_property1 and pms_property2 have the same company company1
                - room_type1 has no company
                - room type room_type2 exists
                - room_type2 has code c1
                - room_type2 has no properties
                - room_type2 has no company
        ACT:    - search room type with code c1 and property pms_property1
                - pms_property1 have company company1
        POST:   - only room_type1 room type found
        """
        # ARRANGE
        room_type1 = self.env["pms.room.type"].create(
            {
                "name": "Room type 1",
                "default_code": "c1",
                "pms_property_ids": [
                    (6, 0, [self.pms_property1.id, self.pms_property3.id])
                ],
                "company_id": False,
                "class_id": self.room_type_class1.id,
            }
        )
        # room_type2
        self.env["pms.room.type"].create(
            {
                "name": "Room type 2",
                "default_code": "c1",
                "pms_property_ids": False,
                "company_id": False,
                "class_id": self.room_type_class1.id,
            }
        )

        # ACT
        room_types = self.env["pms.room.type"].get_room_types_by_property(
            self.pms_property1.id, "c1"
        )

        # ASSERT
        self.assertEqual(room_types.id, room_type1.id, "Expected room type not found")

    def test_multiple_case_02(self):
        """
        PRE:    - room type r1 exists
                - room_type1 has code c1
                - room_type1 has property pms_property1
                - pms_property1 have the company company1
                - room_type1 has no company
                - room type room_type2 exists
                - room_type2 has code c1
                - room_type2 has no properties
                - room_type2 has no company
        ACT:    - search room type with code c1 and property pms_property2
                - pms_property2 have company company1
        POST:   - only room_type1 room type found
        """
        # ARRANGE
        # room_type1
        self.env["pms.room.type"].create(
            {
                "name": "Room type 1",
                "default_code": "c1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
                "company_id": False,
                "class_id": self.room_type_class1.id,
            }
        )
        room_type2 = self.env["pms.room.type"].create(
            {
                "name": "Room type 2",
                "default_code": "c1",
                "pms_property_ids": False,
                "company_id": False,
                "class_id": self.room_type_class1.id,
            }
        )

        # ACT
        room_types = self.env["pms.room.type"].get_room_types_by_property(
            self.pms_property2.id, "c1"
        )

        # ASSERT
        self.assertEqual(room_types.id, room_type2.id, "Expected room type not found")

    def test_multiple_case_03(self):
        """
        PRE:    - room type room_type1 exists
                - room_type1 has code c1
                - room_type1 has property pms_property1
                - pms_property1 have the company company1
                - room_type1 has no company
                - room type room_type2 exists
                - room_type2 has code c1
                - room_type2 has no properties
                - room_type2 has no company
        ACT:    - search room type with code c1 and pms_property3
                - pms_property3 have company2
        POST:   - only room_type2 room type found
        """
        # ARRANGE
        # room_type1
        self.env["pms.room.type"].create(
            {
                "name": "Room type 1",
                "default_code": "c1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
                "company_id": False,
                "class_id": self.room_type_class1.id,
            }
        )
        room_type2 = self.env["pms.room.type"].create(
            {
                "name": "Room type 2",
                "default_code": "c1",
                "pms_property_ids": False,
                "company_id": False,
                "class_id": self.room_type_class1.id,
            }
        )

        # ACT
        room_types = self.env["pms.room.type"].get_room_types_by_property(
            self.pms_property3.id, "c1"
        )

        # ASSERT
        self.assertEqual(room_types.id, room_type2.id, "Expected room type not found")

    def test_multiple_case_04(self):
        """
        PRE:    - room_type1 exists
                - room_type1 has code c1
                - room_type1 has property pms_property1
                - pms_property1 have the company company1
                - room_type1 has no company
                - room_type2 exists
                - room_type2 has code c1
                - room_type2 has no properties
                - room_type2 has company company1
        ACT:    - search room type with code c1 and pms_property3
                - pms_property3 have company2
        POST:   - no room type found
        """
        # ARRANGE
        # room_type1
        self.env["pms.room.type"].create(
            {
                "name": "Room type 1",
                "default_code": "c1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
                "company_id": False,
                "class_id": self.room_type_class1.id,
            }
        )
        # room_type2
        self.env["pms.room.type"].create(
            {
                "name": "Room type 2",
                "default_code": "c1",
                "pms_property_ids": False,
                "company_id": self.company1.id,
                "class_id": self.room_type_class1.id,
            }
        )

        # ACT
        room_types = self.env["pms.room.type"].get_room_types_by_property(
            self.pms_property3.id, "c1"
        )

        # ASSERT
        self.assertFalse(room_types, "Room type found but it should have not found any")

    def test_multiple_case_05(self):
        """
        PRE:    - room_type1 exists
                - room_type1 has code c1
                - room_type1 has property pms_property1
                - pms_property1 have the company company1
                - room_type1 has no company
                - room_type2 exists
                - room_type2 has code c1
                - room_type2 has no properties
                - room_type2 has company2
        ACT:    - search room type with code c1 and pms_property3
                - pms_property3 have company2
        POST:   - room_type2 room type found
        """
        # ARRANGE
        # room_type1
        self.env["pms.room.type"].create(
            {
                "name": "Room type 1",
                "default_code": "c1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
                "company_id": False,
                "class_id": self.room_type_class1.id,
            }
        )
        room_type2 = self.env["pms.room.type"].create(
            {
                "name": "Room type 2",
                "default_code": "c1",
                "pms_property_ids": False,
                "company_id": self.company2.id,
                "class_id": self.room_type_class1.id,
            }
        )

        # ACT
        room_types = self.env["pms.room.type"].get_room_types_by_property(
            self.pms_property3.id, "c1"
        )

        # ASSERT
        self.assertEqual(room_types.id, room_type2.id, "Expected room type not found")

    def test_multiple_case_06(self):
        """
        PRE:    - room type r1 exists
                - room_type1 has code c1
                - room_type1 has property pms_property1
                - pms_property1 have the company company1
                - room_type1 has no company
                - room type r2 exists
                - room_type2 has code c1
                - room_type2 has no properties
                - room_type2 has company company1
                - room type room_type3 exists
                - room_type3 has code c1
                - room_type3 has no properties
                - room_type3 has no company
        ACT:    - search room type with code c1 and pms_property3
                - pms_property3 have company2
        POST:   - room_type3 room type found
        """
        # ARRANGE
        # room_type1
        self.env["pms.room.type"].create(
            {
                "name": "Room type 1",
                "default_code": "c1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
                "company_id": False,
                "class_id": self.room_type_class1.id,
            }
        )
        # room_type2
        self.env["pms.room.type"].create(
            {
                "name": "Room type 2",
                "default_code": "c1",
                "pms_property_ids": False,
                "company_id": self.company1.id,
                "class_id": self.room_type_class1.id,
            }
        )
        room_type3 = self.env["pms.room.type"].create(
            {
                "name": "Room type 3",
                "default_code": "c1",
                "pms_property_ids": False,
                "company_id": False,
                "class_id": self.room_type_class1.id,
            }
        )

        # ACT
        room_types = self.env["pms.room.type"].get_room_types_by_property(
            self.pms_property3.id, "c1"
        )

        # ASSERT
        self.assertEqual(room_types.id, room_type3.id, "Expected room type not found")

    def test_check_property_room_type_class(self):
        # ARRANGE
        room_type_class = self.env["pms.room.type.class"].create(
            {
                "name": "Room Type Class",
                "default_code": "ROOM",
                "pms_property_ids": [
                    (4, self.pms_property2.id),
                ],
            },
        )
        # ACT & ASSERT
        with self.assertRaises(
            UserError, msg="Room Type has been created and it shouldn't"
        ):
            room_type1 = self.env["pms.room.type"].create(
                {
                    "name": "Room Type",
                    "default_code": "c1",
                    "class_id": room_type_class.id,
                    "pms_property_ids": [
                        (4, self.pms_property2.id),
                    ],
                }
            )
            room_type1.pms_property_ids = [(4, self.pms_property1.id)]

    # TODO: pending multi property PR

    # def test_check_board_service_property_integrity(self):
    #
    #     self.room_type_class = self.env["pms.room.type.class"].create(
    #         {"name": "Room Type Class", "default_code": "SIN1"}
    #     )
    #     self.room_type = self.env["pms.room.type"].create(
    #        {
    #             "name": "Room Type",
    #             "default_code": "Type1",
    #            "pms_property_ids": self.p3,
    #            "class_id": self.room_type_class.id,
    #        }
    #        )
    #     self.board_service = self.env["pms.board.service"].create(
    #        {
    #            "name": "Board Service",
    #        }
    #     )
    #     with self.assertRaises(ValidationError):
    #         self.env["pms.board.service.room.type"].create(
    #             {
    #                 "pms_board_service_id": self.board_service.id,
    #                 "pms_room_type_id": self.room_type.id,
    #                 "pricelist_id": self.env.ref("product.list0").id,
    #                 "pms_property_ids": self.p4,
    #             }
    #         )

    def test_check_amenities_property_integrity(self):
        self.amenity1 = self.env["pms.amenity"].create(
            {"name": "Amenity", "pms_property_ids": self.pms_property1}
        )
        with self.assertRaises(UserError):
            self.env["pms.room.type"].create(
                {
                    "name": "Room Type",
                    "default_code": "Type1",
                    "class_id": self.room_type_class1.id,
                    "pms_property_ids": [self.pms_property2.id],
                    "room_amenity_ids": [self.amenity1.id],
                }
            )
