# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError

from .common import TestPms


class TestRoomTypeClass(TestPms):
    def setUp(self):
        super().setUp()
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

    # external integrity
    def test_external_case_01(self):
        """
        PRE:    - room type class cl1 exists
                - room_type_class1 has code c1
                - room_type_class1 has pms_property1
                - pms_property1 has company company1
        ACT:    - create a new room_type_class2 class
                - room_type_class2 has code c1
                - room_type_class2 has pms_property1
                - pms_property1 has company company1
        POST:   - Integrity error: the room type already exists
                - room_type_class2 not created
        """
        # ARRANGE
        # room_type_class1
        self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl1",
                "default_code": "c1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
            }
        )

        # ACT & ASSERT
        with self.assertRaises(
            ValidationError, msg="The room type class has been created and it shouldn't"
        ):
            # room_type_class2
            self.env["pms.room.type.class"].create(
                {
                    "name": "Room type class cl2",
                    "default_code": "c1",
                    "pms_property_ids": [(6, 0, [self.pms_property1.id])],
                }
            )

    def test_external_case_02(self):
        """
        PRE:    - room type class cl1 exists
                - room_type_class1 has code c1
                - room_type_class1 has property pms_property1
                - pms_property1 has company company1
        ACT:    - create a new room_type_class2 class
                - room_type_class2 has code c1
                - room_type_class2 has property pms_property1, pms_property2,
                    pms_property3
                - pms_property1, pms_property2 has company company1
                - pms_property3 has company company2
        POST:   - Integrity error: the room type class already exists
                - room_type_class2 not created
        """
        # ARRANGE
        self.pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        # room_type_class1
        self.env["pms.room.type.class"].create(
            {
                "name": "Room type class 1",
                "default_code": "c1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
            }
        )

        # ACT & ASSERT
        with self.assertRaises(
            ValidationError, msg="The room type class has been created and it shouldn't"
        ):
            # room_type_class2
            self.env["pms.room.type.class"].create(
                {
                    "name": "Room type class cl2",
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
                }
            )

    def test_single_case_01(self):
        """
        PRE:    - room type class cl1 exists
                - room_type_class1 has code c1
                - room_type_class1 has 2 properties pms_property1 and pms_property2
                - pms_property_1 and pms_property2 have the same company company1
        ACT:    - search room type class with code c1 and pms_property1
                - pms_property1 has company company1
        POST:   - only room_type_class1 room type class found
        """
        # ARRANGE
        room_type_class1 = self.env["pms.room.type.class"].create(
            {
                "name": "Room type class 1",
                "default_code": "c1",
                "pms_property_ids": [
                    (6, 0, [self.pms_property1.id, self.pms_property3.id])
                ],
            }
        )

        # ACT
        room_type_classes = self.env["pms.room.type.class"].get_unique_by_property_code(
            self.pms_property1.id, "c1"
        )

        # ASSERT
        self.assertEqual(
            room_type_classes.id,
            room_type_class1.id,
            "Expected room type class not found",
        )

    def test_single_case_02(self):
        """
        PRE:    - room type class cl1 exists
                - room_type_class1 has code c1
                - room_type_class1 has 2 properties pms_property1 and pms_property3
                - pms_property1 and pms_property2 have different companies
                - pms_property1 have company company1 and pms_property3 have company2
        ACT:    - search room type class with code c1 and property pms_property1
                - pms_property1 has company company1
        POST:   - only room_type_class1 room type found
        """
        # ARRANGE
        cl1 = self.env["pms.room.type.class"].create(
            {
                "name": "Room type class 1",
                "default_code": "c1",
                "pms_property_ids": [
                    (6, 0, [self.pms_property1.id, self.pms_property3.id])
                ],
            }
        )

        # ACT
        room_type_classes = self.env["pms.room.type.class"].get_unique_by_property_code(
            self.pms_property1.id, "c1"
        )

        # ASSERT
        self.assertEqual(
            room_type_classes.id, cl1.id, "Expected room type class not found"
        )

    def test_single_case_03(self):
        """
        PRE:    - room_type_class1 exists
                - room_type_class1 has code c1
                - room_type_class1 with 2 properties pms_property1 and pms_property2
                - pms_property1 and pms_property2 have same company company1
        ACT:    - search room type class with code c1 and property pms_property3
                - pms_property3 have company company2
        POST:   - no room type found
        """
        # ARRANGE
        self.pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        # room_type_class1
        self.env["pms.room.type.class"].create(
            {
                "name": "Room type class 1",
                "default_code": "c1",
                "pms_property_ids": [
                    (6, 0, [self.pms_property1.id, self.pms_property2.id])
                ],
            }
        )

        # ACT
        room_type_classes = self.env["pms.room.type.class"].get_unique_by_property_code(
            self.pms_property3.id, "c1"
        )

        # ASSERT
        self.assertFalse(
            room_type_classes, "Room type class found but it should not have found any"
        )

    def test_single_case_04(self):
        """
        PRE:    - room_type_class1 exists
                - room_type_class1 has code c1
                - room_type_class1 properties are null
        ACT:    - search room type class with code c1 and property pms_property1
                - pms_property1 have company company1
        POST:   - only room_type_class1 room type class found
        """
        # ARRANGE
        room_type_class1 = self.env["pms.room.type.class"].create(
            {
                "name": "Room type class 1",
                "default_code": "c1",
                "pms_property_ids": False,
            }
        )

        # ACT
        room_type_classes = self.env["pms.room.type.class"].get_unique_by_property_code(
            self.pms_property1.id, "c1"
        )

        # ASSERT
        self.assertEqual(
            room_type_classes.id,
            room_type_class1.id,
            "Expected room type class not found",
        )

    # tests with more than one room type class
    def test_multiple_case_01(self):
        """
        PRE:    - room_type_class1 exists
                - room_type_class1 has code c1
                - room_type_class1 has 2 properties pms_property1 and pms_property2
                - pms_property1 and pms_property2 have the same company company1
                - room type class room_type_class2 exists
                - room_type_class2 has code c1
                - room_type_class2 has no properties
        ACT:    - search room type class with code c1 and property pms_property1
                - pms_property1 have company company1
        POST:   - only room_type_class1 room type class found
        """
        # ARRANGE
        room_type_class1 = self.env["pms.room.type.class"].create(
            {
                "name": "Room type class 1",
                "default_code": "c1",
                "pms_property_ids": [
                    (6, 0, [self.pms_property1.id, self.pms_property3.id])
                ],
            }
        )
        # room_type_class2
        self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl2",
                "default_code": "c1",
                "pms_property_ids": False,
            }
        )

        # ACT
        room_type_classes = self.env["pms.room.type.class"].get_unique_by_property_code(
            self.pms_property1.id, "c1"
        )

        # ASSERT
        self.assertEqual(
            room_type_classes.id,
            room_type_class1.id,
            "Expected room type class not found",
        )

    def test_multiple_case_02(self):
        """
        PRE:    - room_type_class1 exists
                - room_type_class1 has code c1
                - room_type_class1 has property pms_property1
                - pms_property1 have the company company1
                - room type class room_type_class2 exists
                - room_type_class2 has code c1
                - room_type_class2 has no properties
        ACT:    - search room type class with code c1 and pms_property2
                - pms_property2 have company company1
        POST:   - only room_type_class1 room type class found
        """
        # ARRANGE
        self.pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        # room_type_class1
        self.env["pms.room.type.class"].create(
            {
                "name": "Room type class 1",
                "default_code": "c1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
            }
        )
        room_type_class2 = self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl2",
                "default_code": "c1",
                "pms_property_ids": False,
            }
        )

        # ACT
        room_type_classes = self.env["pms.room.type.class"].get_unique_by_property_code(
            self.pms_property2.id, "c1"
        )

        # ASSERT
        self.assertEqual(
            room_type_classes.id,
            room_type_class2.id,
            "Expected room type class not found",
        )

    def test_multiple_case_03(self):
        """
        PRE:    - room_type_class1 exists
                - room_type_class1 has code c1
                - room_type_class1 has property pms_property1
                - pms_property1 have the company company1
                - room type class room_type_class2 exists
                - room_type_class2 has code c1
                - room_type_class2 has no properties
        ACT:    - search room type class with code c1 and property pms_property3
                - pms_property3 have company company2
        POST:   - only room_type_class2 room type class found
        """
        # ARRANGE
        # room_type_class1
        self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl1",
                "default_code": "c1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
            }
        )
        room_type_class2 = self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl2",
                "default_code": "c1",
                "pms_property_ids": False,
            }
        )

        # ACT
        room_type_classes = self.env["pms.room.type.class"].get_unique_by_property_code(
            self.pms_property3.id, "c1"
        )

        # ASSERT
        self.assertEqual(
            room_type_classes.id,
            room_type_class2.id,
            "Expected room type class not found",
        )

    def test_multiple_case_04(self):
        """
        PRE:    - room_type_class1 exists
                - room_type_class1 has code c1
                - room_type_class1 has property pms_property1
                - pms_property1 have the company company1
                - room type room_type_class2 exists
                - room_type_class2 has code c1
                - room_type_class2 has no properties
        ACT:    - search room type class with code c1 and property pms_property3
                - pms_property3 have company company2
        POST:   - r2 room type class found
        """
        # ARRANGE
        # room_type_class1
        self.env["pms.room.type.class"].create(
            {
                "name": "Room type class 1",
                "default_code": "c1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
            }
        )
        room_type_class2 = self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl2",
                "default_code": "c1",
                "pms_property_ids": False,
            }
        )

        # ACT
        room_type_classes = self.env["pms.room.type.class"].get_unique_by_property_code(
            self.pms_property3.id, "c1"
        )

        # ASSERT
        self.assertEqual(
            room_type_classes.id, room_type_class2.id, "Expected room type not found"
        )
