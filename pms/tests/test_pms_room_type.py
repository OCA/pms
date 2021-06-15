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

    def test_create_room_type_consistency_company(self):
        """
        Create a room type with a company (1) consistent with the company property (1).
        Creation should be successful.

        PRE:    - room_type1 does not exists
        ACT:    - create a new room_type1 room
                - room_type1 has code c1
                - room_type1 has property pms_property1
                - pms_property1 has company company1
                - room_type1 has company company1
        POST:   - room_type1 created
        """
        # ARRANGE & ACT
        new_room_type = self.env["pms.room.type"].create(
            {
                "name": "Room type 1",
                "default_code": "c1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
                "company_id": self.company1.id,
                "class_id": self.room_type_class1.id,
            }
        )
        # ASSERT
        self.assertTrue(new_room_type.id, "Room type not created when it should")

    def test_create_room_type_inconsistency_company(self):
        """
        Create a room type with inconsistency between company (1)
        and company property (1).
        The creation should fail.

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

    def test_create_room_type_inconsistency_companies(self):
        """
        Create a room type with inconsistency between company (1)
        and company properties (several).
        The creation should fail.

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

    def test_create_room_type_consistency_companies(self):
        """
        Create a room type with consistency between companies (all)
        and company properties (2).
        Creation should be successful.

        PRE:    - room_type1 does not exists
        ACT:    - create a new room_type1
                - room_type1 has code c1
                - room_type1 has property pms_property1 and pms_property3
                - pms_property1 has company company1
                - pms_property3 has company2
                - room_type1 has no company
        POST:   - room_type1 created
        """
        # ARRANGE & ACT
        new_room_type = self.env["pms.room.type"].create(
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
        # ASSERT
        self.assertTrue(new_room_type.id, "Room type not created when it should")

    # external integrity
    def test_create_room_type_inconsistency_all_companies(self):
        """
        Create a room type for 1 company and 1 property.
        Try to create a room type for all the companies.
        The creation should fail.

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

    def test_create_room_type_inconsistency_code_company(self):
        """
        Create a room type for all the companies and for one property.
        Try to create a room type with same code and same property but
        for all companies.
        The creation should fail.

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

    def test_create_room_type_inconsistency_code_companies(self):
        """
        Create a room type for 1 property and 1 company.
        Try to create a room type with same code and 3 propertys
        belonging to 2 different companies.
        The creation should fail.

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

    def test_get_room_type_by_property_first(self):
        """
        Room type exists for all the companies and 2 properties.
        Search for property of existing room type.
        The method should return the existing room type.

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

    def test_get_room_type_by_property_second(self):
        """
        Room type exists for all the companies and 2 properties.
        Search for 2nd property of existing room type.
        The method should return existing room type.

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

    def test_get_room_type_by_property_existing_all_same_company(self):
        """
        Room type exists for 1 company and for all properties.
        Search for one specific property belonging to same company
        as the existing room type.
        The method should return existing room type.

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

    def test_get_room_type_by_property_existing_all_diff_company(self):
        """
        Room type exists for 1 company and all the properties.
        Search for property different than existing room type.
        The method shouldn't return results.

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
    def test_get_room_type_by_property_existing_several_match_prop(self):
        """
        Room type 1 exists for all companies and 2 properties.
        Room type 2 exists for all companies and properties.
        Search for same property as one of the 1st room type created.
        The method should return the 1st room type created.

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

    def test_get_room_type_by_property_diff_company(self):
        """
        Room type 1 exists for all companies and one property.
        Room type 2 exists for all companies and properties.
        Search for property different than the 1st room type created
        and belonging to different company.
        The method should return the 2nd room type created.

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

    def test_get_room_type_by_property_same_company(self):
        """
        Room type 1 exists for all companies and one property.
        Room type 2 exists for all companies and properties.
        Search for property different than the 1st room type created
        and belonging to same company.
        The method should return the 2nd room type created.

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

    def test_get_room_type_by_property_same_company_prop_not_found(self):
        """
        Room type 1 exists for all companies and one property.
        Room type 2 exists for one company and for all properties.
        Search for property different than the
        1st room type created but belonging to same company.
        The method shouldn't return results.

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

    def test_get_room_type_by_property_same_company_prop(self):
        """
        Room type 1 exists for all companies and for one property.
        Room type 2 exists for one company and for all properties.
        Search for property belonging to the same company as
        2nd room type created.
        The method should return 2nd existing room type.

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

    def test_get_room_type_by_property_diff_company_prop(self):
        """
        Room type 1 exists for all companies and for one property.
        Room type 2 exists for one company and for all properties.
        Room type 3 exists for all companies and for all properties.
        Search for property belonging to a different company than
        the 2nd room type created.
        The method should return 3rd room type.

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

    def test_rooom_type_creation_inconsistency_class(self):
        """
        Create a rooom type class  belonging to one property.
        Create a room type belonging to another property.
        Room type creation should fail.
        """
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

    def test_rooom_type_creation_consistency_class(self):
        """
        Create a rooom type class  belonging to one property.
        Create a room type belonging to same property.
        Room type creation should be successful.
        """
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
        # ACT
        new_room_type = self.env["pms.room.type"].create(
            {
                "name": "Room Type",
                "default_code": "c1",
                "class_id": room_type_class.id,
                "pms_property_ids": [
                    (4, self.pms_property2.id),
                ],
            }
        )
        # ASSERT
        self.assertTrue(new_room_type.id, "Room type creation should be successful.")

    def test_check_board_service_property_integrity(self):
        # ARRANGE
        room_type = self.env["pms.room.type"].create(
            {
                "name": "Room Type",
                "default_code": "Type1",
                "pms_property_ids": self.pms_property1,
                "class_id": self.room_type_class1.id,
            }
        )
        board_service = self.env["pms.board.service"].create(
            {
                "name": "Board service 1",
                "default_code": "c1",
                "pms_property_ids": self.pms_property1,
            }
        )
        # ACT & ASSERT
        with self.assertRaises(UserError, msg="Board service created and shouldn't."):
            self.env["pms.board.service.room.type"].create(
                {
                    "pms_board_service_id": board_service.id,
                    "pms_room_type_id": room_type.id,
                    "pms_property_ids": self.pms_property2,
                }
            )

    def test_check_amenities_property_integrity(self):
        self.amenity1 = self.env["pms.amenity"].create(
            {"name": "Amenity", "pms_property_ids": self.pms_property1}
        )
        # ACT & ASSERT
        with self.assertRaises(
            UserError,
            msg="Shouldn't create room type with amenities belonging to other properties",
        ):
            self.env["pms.room.type"].create(
                {
                    "name": "Room Type",
                    "default_code": "Type1",
                    "class_id": self.room_type_class1.id,
                    "pms_property_ids": [self.pms_property2.id],
                    "room_amenity_ids": [self.amenity1.id],
                }
            )

    def test_rooom_type_creation_consistency_amenity(self):
        """
        Create an amenity belonging to one property.
        Create a room type belonging to same property.
        Room type creation should be successful.
        """
        # ARRANGE
        self.amenity1 = self.env["pms.amenity"].create(
            {"name": "Amenity", "pms_property_ids": self.pms_property1}
        )
        # ACT
        new_room_type = self.env["pms.room.type"].create(
            {
                "name": "Room Type",
                "default_code": "Type1",
                "class_id": self.room_type_class1.id,
                "pms_property_ids": [self.pms_property1.id],
                "room_amenity_ids": [self.amenity1.id],
            }
        )
        # ASSERT
        self.assertTrue(new_room_type.id, "Room type creation should be successful.")
