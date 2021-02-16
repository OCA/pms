# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import SavepointCase


class TestRoomTypeClass(SavepointCase):
    def setUp(self):
        super().setUp()
        self.p1 = self.browse_ref("pms.main_pms_property")
        self.m1 = self.p1.company_id
        self.p2 = self.env["pms.property"].create(
            {
                "name": "p2",
                "company_id": self.m1.id,
                "default_pricelist_id": self.ref("product.list0"),
            }
        )
        self.m2 = self.env["res.company"].create(
            {
                "name": "Company m2",
            }
        )
        self.p3 = self.env["pms.property"].create(
            {
                "name": "p3",
                "company_id": self.m2.id,
                "default_pricelist_id": self.ref("product.list0"),
            }
        )


class TestRoomTypeClassCodePropertyIntegrity(TestRoomTypeClass):
    # external integrity
    def test_external_case_01(self):
        """
        PRE:    - room type class cl1 exists
                - cl1 has code c1
                - cl1 has property p1
                - p1 has company m1
        ACT:    - create a new cl2 class
                - cl2 has code c1
                - cl2 has property p1
                - p1 has company m1
        POST:   - Integrity error: the room type already exists
                - cl2 not created
        """
        # ARRANGE
        # cl1
        self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl1",
                "code_class": "c1",
                "pms_property_ids": [(6, 0, [self.p1.id])],
            }
        )

        # ACT & ASSERT
        with self.assertRaises(
            ValidationError, msg="The room type class has been created and it shouldn't"
        ):
            # cl2
            self.env["pms.room.type.class"].create(
                {
                    "name": "Room type class cl2",
                    "code_class": "c1",
                    "pms_property_ids": [(6, 0, [self.p1.id])],
                }
            )

    def test_external_case_02(self):
        """
        PRE:    - room type class cl1 exists
                - cl1 has code c1
                - cl1 has property p1
                - p1 has company m1
        ACT:    - create a new cl2 class
                - cl2 has code c1
                - cl2 has property p1, p2, p3
                - p1, p2 has company m1
                - p3 has company m2
        POST:   - Integrity error: the room type class already exists
                - cl2 not created
        """
        # ARRANGE
        # cl1
        self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl1",
                "code_class": "c1",
                "pms_property_ids": [(6, 0, [self.p1.id])],
            }
        )

        # ACT & ASSERT
        with self.assertRaises(
            ValidationError, msg="The room type class has been created and it shouldn't"
        ):
            # cl2
            self.env["pms.room.type.class"].create(
                {
                    "name": "Room type class cl2",
                    "code_class": "c1",
                    "pms_property_ids": [(6, 0, [self.p1.id, self.p2.id, self.p3.id])],
                }
            )


class TestRoomTypeClassCodePropertyUniqueness(TestRoomTypeClass):
    # test with one room type class
    def test_single_case_01(self):
        """
        PRE:    - room type class cl1 exists
                - cl1 has code c1
                - cl1 has 2 properties p1 and p2
                - p1 and p2 have the same company m1
        ACT:    - search room type class with code c1 and property p1
                - p1 has company m1
        POST:   - only cl1 room type class found
        """
        # ARRANGE
        cl1 = self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl1",
                "code_class": "c1",
                "pms_property_ids": [(6, 0, [self.p1.id, self.p3.id])],
            }
        )

        # ACT
        room_type_class = self.env["pms.room.type.class"].get_unique_by_property_code(
            self.p1.id, "c1"
        )

        # ASSERT
        self.assertEqual(
            room_type_class.id, cl1.id, "Expected room type class not found"
        )

    def test_single_case_02(self):
        """
        PRE:    - room type class cl1 exists
                - cl1 has code c1
                - cl1 has 2 properties p1 and p3
                - p1 and p2 have different companies
                - p1 have company m1 and p3 have company m2
        ACT:    - search room type class with code c1 and property p1
                - p1 has company m1
        POST:   - only cl1 room type found
        """
        # ARRANGE
        cl1 = self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl1",
                "code_class": "c1",
                "pms_property_ids": [(6, 0, [self.p1.id, self.p3.id])],
            }
        )

        # ACT
        room_type_class = self.env["pms.room.type.class"].get_unique_by_property_code(
            self.p1.id, "c1"
        )

        # ASSERT
        self.assertEqual(
            room_type_class.id, cl1.id, "Expected room type class not found"
        )

    def test_single_case_03(self):
        """
        PRE:    - room type class cl1 exists
                - cl1 has code c1
                - cl1 with 2 properties p1 and p2
                - p1 and p2 have same company m1
        ACT:    - search room type class with code c1 and property p3
                - p3 have company m2
        POST:   - no room type found
        """
        # ARRANGE
        # cl1
        self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl1",
                "code_class": "c1",
                "pms_property_ids": [(6, 0, [self.p1.id, self.p2.id])],
            }
        )

        # ACT
        room_type_class = self.env["pms.room.type.class"].get_unique_by_property_code(
            self.p3.id, "c1"
        )

        # ASSERT
        self.assertFalse(
            room_type_class, "Room type class found but it should not have found any"
        )

    def test_single_case_04(self):
        """
        PRE:    - room type class cl1 exists
                - cl1 has code c1
                - cl1 properties are null
        ACT:    - search room type class with code c1 and property p1
                - p1 have company m1
        POST:   - only cl1 room type class found
        """
        # ARRANGE
        cl1 = self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl1",
                "code_class": "c1",
                "pms_property_ids": False,
            }
        )

        # ACT
        room_type_class = self.env["pms.room.type.class"].get_unique_by_property_code(
            self.p1.id, "c1"
        )

        # ASSERT
        self.assertEqual(
            room_type_class.id, cl1.id, "Expected room type class not found"
        )

    # tests with more than one room type class
    def test_multiple_case_01(self):
        """
        PRE:    - room type class cl1 exists
                - cl1 has code c1
                - cl1 has 2 properties p1 and p2
                - p1 and p2 have the same company m1
                - room type class cl2 exists
                - cl2 has code c1
                - cl2 has no properties
        ACT:    - search room type class with code c1 and property p1
                - p1 have company m1
        POST:   - only cl1 room type class found
        """
        # ARRANGE
        cl1 = self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl1",
                "code_class": "c1",
                "pms_property_ids": [(6, 0, [self.p1.id, self.p3.id])],
            }
        )
        # cl2
        self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl2",
                "code_class": "c1",
                "pms_property_ids": False,
            }
        )

        # ACT
        room_type_class = self.env["pms.room.type.class"].get_unique_by_property_code(
            self.p1.id, "c1"
        )

        # ASSERT
        self.assertEqual(
            room_type_class.id, cl1.id, "Expected room type class not found"
        )

    def test_multiple_case_02(self):
        """
        PRE:    - room type class cl1 exists
                - cl1 has code c1
                - cl1 has property p1
                - p1 have the company m1
                - room type class cl2 exists
                - cl2 has code c1
                - cl2 has no properties
        ACT:    - search room type class with code c1 and property p2
                - p2 have company m1
        POST:   - only cl1 room type class found
        """
        # ARRANGE
        # cl1
        self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl1",
                "code_class": "c1",
                "pms_property_ids": [(6, 0, [self.p1.id])],
            }
        )
        cl2 = self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl2",
                "code_class": "c1",
                "pms_property_ids": False,
            }
        )

        # ACT
        room_type_class = self.env["pms.room.type.class"].get_unique_by_property_code(
            self.p2.id, "c1"
        )

        # ASSERT
        self.assertEqual(
            room_type_class.id, cl2.id, "Expected room type class not found"
        )

    def test_multiple_case_03(self):
        """
        PRE:    - room type class cl1 exists
                - cl1 has code c1
                - cl1 has property p1
                - p1 have the company m1
                - room type class cl2 exists
                - cl2 has code c1
                - cl2 has no properties
        ACT:    - search room type class with code c1 and property p3
                - p3 have company m2
        POST:   - only cl2 room type class found
        """
        # ARRANGE
        # cl1
        self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl1",
                "code_class": "c1",
                "pms_property_ids": [(6, 0, [self.p1.id])],
            }
        )
        cl2 = self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl2",
                "code_class": "c1",
                "pms_property_ids": False,
            }
        )

        # ACT
        room_type_class = self.env["pms.room.type.class"].get_unique_by_property_code(
            self.p3.id, "c1"
        )

        # ASSERT
        self.assertEqual(
            room_type_class.id, cl2.id, "Expected room type class not found"
        )

    def test_multiple_case_04(self):
        """
        PRE:    - room type class cl1 exists
                - cl1 has code c1
                - cl1 has property p1
                - p1 have the company m1
                - room type cl2 exists
                - cl2 has code c1
                - cl2 has no properties
        ACT:    - search room type class with code c1 and property p3
                - p3 have company m2
        POST:   - r2 room type class found
        """
        # ARRANGE
        # cl1
        self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl1",
                "code_class": "c1",
                "pms_property_ids": [(6, 0, [self.p1.id])],
            }
        )
        cl2 = self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl2",
                "code_class": "c1",
                "pms_property_ids": False,
            }
        )

        # ACT
        room_type_class = self.env["pms.room.type.class"].get_unique_by_property_code(
            self.p3.id, "c1"
        )

        # ASSERT
        self.assertEqual(room_type_class.id, cl2.id, "Expected room type not found")
