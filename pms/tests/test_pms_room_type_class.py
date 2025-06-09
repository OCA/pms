# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError

from .common import TestPms


class TestRoomTypeClass(TestPms):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company2 = cls.env["res.company"].create(
            {
                "name": "Company 2",
            }
        )
        cls.pms_property3 = cls.env["pms.property"].create(
            {
                "name": "Property 3",
                "company_id": cls.company2.id,
                "default_pricelist_id": cls.pricelist1.id,
            }
        )

    # external integrity
    def test_external_case_01(self):
        """
        Check that a room type class cannot be created with an existing default_code
        in the same property.
        ----------
        A room type class is created with the default_code = 'c1' in property pms_property1.
        Then try to create another room type class in the same property with the same code,
        but this should throw a ValidationError.
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
        Check that a room type class cannot be created with an existing default_code
        in the same property.
        ----------
        A room type class is created with the default_code = 'c1' in property pms_property1.
        Then try to create another room type class with the same code in 3 properties and one
        of them is the same property in which the other room type class was
        created(pms_property1), but this should throw a ValidationError.
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
        Check that the room type class was created correctly and that
        it is in the property in which it was searched through its default code.
        -----------
        Create a room type class with default code as 'c1' for properties 1 and 3
        (different companies), save the value returned by the get_unique_by_property_code()
        method, passing  property1 and default_code 'c1' as parameters. It is checked
        that the id of the room type class created and the id of the record returned by the
        method match.
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
        Check that the room type class was created correctly and that
        it is in the property in which it was searched through its default code.
        -----------
        Create a room type class with default code as 'c1' for properties 1 and 3
        (same company), save the value returned by the get_unique_by_property_code()
        method, passing  property1 and default_code 'c1' as parameters. It is checked
        that the id of the room type class created and the id of the record returned by the
        method  match.
        """
        # ARRANGE
        self.pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        cl1 = self.env["pms.room.type.class"].create(
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
            self.pms_property1.id, "c1"
        )

        # ASSERT
        self.assertEqual(
            room_type_classes.id, cl1.id, "Expected room type class not found"
        )

    def test_single_case_03(self):
        """
        Check that a room type class created for a property is not
        found in another property with a different company.
        -----------
        A room type class is created with default_code 'c1' for properties
        1 and 2. It is searched through get_unique_by_property_code()
        passing it as parameters 'c1' and property 3 (from a different
        company than 1 and 2). It is verified that that room type class
        does not exist in that property.
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
        Check that a room type class with properties = False
        (all properties) is found by searching for it in one
        of the properties.
        --------------
        A room type is created with default code = 'c1' and with
        pms_property_ids = False. The room_type_class with
        code 'c1' in property 1 is searched through the
        get_unique_by_property_code() method and it is verified
        that the returned value is correct.
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
        Check that a room type class can be created with the same
        code as another when one of them has pms_property_ids = False
        ------------
        A room type class is created with code 'c1' for properties 1 and 3.
        Another room type class is created with code 'c1' and the properties
        set to False. The room_type with code 'c1' in property 1 is
        searched through the get_unique_by_property_code() method and it is
        verified that the returned value is correct.
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
        Check that a room type class can be created with the same
        code as another when one of them has pms_property_ids = False
        ----------
        A room type class is created with code 'c1' for property 1(company1).
        Another room type class is created with code 'c1' and the
        properties set to False. Then the room_type with code 'c1'
        in property 2(company1) is searched through the
        get_unique_by_property_code() method and the result is checked.
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
        Check that a room type class can be created with the same
        code as another when one of them has pms_property_ids = False
        ----------
        A room type class is created with code 'c1' for property 1(company1).
        Another room type class is created with code 'c1' and the
        properties set to False. Then the room_type with code 'c1'
        in property 3(company2) is searched through the
        get_unique_by_property_code() method and the result is checked.
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
