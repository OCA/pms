from odoo.exceptions import ValidationError

from .common import TestPms


class TestPmsResUser(TestPms):
    def setUp(self):
        super().setUp()
        # create a company and properties
        self.company_A = self.env["res.company"].create(
            {
                "name": "Pms_Company1",
            }
        )
        self.company_B = self.env["res.company"].create(
            {
                "name": "Pms_Company2",
            }
        )
        self.property_A1 = self.env["pms.property"].create(
            {
                "name": "Pms_property",
                "company_id": self.company_A.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        self.property_A2 = self.env["pms.property"].create(
            {
                "name": "Pms_property2",
                "company_id": self.company_A.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        self.property_B1 = self.env["pms.property"].create(
            {
                "name": "Pms_propertyB1",
                "company_id": self.company_B.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )

    def test_property_not_in_allowed_properties(self):
        """
        Property not allowed for the user
        Check a user cannot have an active property
        that is not in the allowed properties

        Company_A ---> Property_A1, Property_A2
        Company_B ---> Property_B1


        """
        # ARRANGE
        Users = self.env["res.users"]
        # ACT & ASSERT
        with self.assertRaises(
            ValidationError,
            msg="Some property is not included in the allowed properties",
        ):
            Users.create(
                {
                    "name": "Test User",
                    "login": "test_user",
                    "company_ids": [(4, self.company_A.id)],
                    "company_id": self.company_A.id,
                    "pms_property_ids": [(4, self.property_A1.id)],
                    "pms_property_id": self.property_B1.id,
                }
            )

    def test_property_not_in_allowed_companies(self):
        """
        Property not allowed for the user
        Check a user cannot have a property in allowed properties
        that does not belong to their companies

        Company_A ---> Property_A1, Property_A2
        Company_B ---> Property_B1

        """
        # ARRANGE
        Users = self.env["res.users"]
        # ACT & ASSERT
        with self.assertRaises(
            ValidationError, msg="Some property doesn't belong to the allowed companies"
        ):
            Users.create(
                {
                    "name": "Test User",
                    "login": "test_user",
                    "company_ids": [(4, self.company_A.id)],
                    "company_id": self.company_A.id,
                    "pms_property_ids": [
                        (4, self.property_A1.id),
                        (4, self.property_B1.id),
                    ],
                    "pms_property_id": self.property_A1.id,
                }
            )

    def test_property_in_allowed_properties(self):
        """
        Successful user creation
        Check user creation with active property in allowed properties

        Company_A ---> Property_A1, Property_A2
        Company_B ---> Property_B1

        """
        # ARRANGE
        Users = self.env["res.users"]
        # ACT
        user1 = Users.create(
            {
                "name": "Test User",
                "login": "test_user",
                "company_ids": [(4, self.company_A.id)],
                "company_id": self.company_A.id,
                "pms_property_ids": [
                    (4, self.property_A1.id),
                    (4, self.property_A2.id),
                ],
                "pms_property_id": self.property_A1.id,
            }
        )
        # ASSERT
        self.assertIn(
            user1.pms_property_id,
            user1.pms_property_ids,
            "Active property not in allowed properties",
        )

    def test_properties_belong_to_companies(self):
        """
        Successful user creation
        Check user creation with active property and allowed properties
        belonging to the allowed companies

        Company_A ---> Property_A1, Property_A2
        Company_B ---> Property_B1

        """
        # ARRANGE
        Users = self.env["res.users"]
        # ACT
        user1 = Users.create(
            {
                "name": "Test User",
                "login": "test_user",
                "company_ids": [(4, self.company_A.id)],
                "company_id": self.company_A.id,
                "pms_property_ids": [
                    (4, self.property_A1.id),
                    (4, self.property_A2.id),
                ],
                "pms_property_id": self.property_A1.id,
            }
        )
        # ASSERT
        self.assertEqual(
            user1.pms_property_id.company_id,
            user1.company_id,
            "Active property doesn't belong to active company",
        )
