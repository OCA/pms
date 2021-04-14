from odoo.exceptions import ValidationError

from .common import TestPms


class TestPmsAmenity(TestPms):
    def setUp(self):
        super().setUp()
        # Create two properties
        # +-----------+-----------+
        # |      Properties       |
        # +-----------+-----------+
        # | Property2 - Property3 |
        # +-----------+-----------+

        self.pms_property2 = self.env["pms.property"].create(
            {
                "name": "Pms_property_test2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )

        self.pms_property3 = self.env["pms.property"].create(
            {
                "name": "Pms_property_test3",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )

    def test_property_not_allowed(self):
        # Creation of a Amenity with Properties incompatible with it Amenity Type

        # +-----------------------------------+-----------------------------------+
        # |  Amenity Type (TestAmenityType1)  |      Amenity (TestAmenity1)       |
        # +-----------------------------------+-----------------------------------+
        # |      Property1 - Property2        | Property1 - Property2 - Property3 |
        # +-----------------------------------+-----------------------------------+

        # ARRANGE
        AmenityType = self.env["pms.amenity.type"]
        Amenity = self.env["pms.amenity"]
        amenity_type1 = AmenityType.create(
            {
                "name": "TestAmenityType1",
                "pms_property_ids": [
                    (4, self.pms_property1.id),
                    (4, self.pms_property2.id),
                ],
            }
        )
        # ACT & ASSERT
        with self.assertRaises(ValidationError), self.cr.savepoint():
            Amenity.create(
                {
                    "name": "TestAmenity1",
                    "pms_amenity_type_id": amenity_type1.id,
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

    def test_property_allowed(self):
        # Creation of a Amenity with Properties compatible with it Amenity Type
        # Check Properties of Amenity are in Properties of Amenity Type
        # +----------------------------------------+-----------------------------------+
        # |     Amenity Type (TestAmenityType1)    |      Amenity (TestAmenity1)       |
        # +----------------------------------------+-----------------------------------+
        # |    Property1 - Property2 - Property3   | Property1 - Property2 - Property3 |
        # +----------------------------------------+-----------------------------------+

        # ARRANGE
        AmenityType = self.env["pms.amenity.type"]
        Amenity = self.env["pms.amenity"]
        amenity_type1 = AmenityType.create(
            {
                "name": "TestAmenityType1",
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
        # ACT
        amenity1 = Amenity.create(
            {
                "name": "TestAmenity1",
                "pms_amenity_type_id": amenity_type1.id,
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

        # ASSERT
        self.assertEqual(
            amenity1.pms_property_ids.ids,
            amenity_type1.pms_property_ids.ids,
            "Properties not allowed in amenity type",
        )

    def test_change_amenity_property(self):
        # Creation of a Amenity with Properties compatible with it Amenity Type
        # Delete a Property in Amenity Type, check Validation Error when do that
        # 1st scenario:
        # +----------------------------------------+-----------------------------------+
        # |     Amenity Type (TestAmenityType1)    |      Amenity (TestAmenity1)       |
        # +----------------------------------------+-----------------------------------+
        # |    Property1 - Property2 - Property3   | Property1 - Property2 - Property3 |
        # +----------------------------------------+-----------------------------------+
        # 2nd scenario(Error):
        # +----------------------------------------+-----------------------------------+
        # |     Amenity Type (TestAmenityType1)    |      Amenity (TestAmenity1)       |
        # +----------------------------------------+-----------------------------------+
        # |          Property1 - Property2         | Property1 - Property2 - Property3 |
        # +----------------------------------------+-----------------------------------+

        # ARRANGE
        AmenityType = self.env["pms.amenity.type"]
        Amenity = self.env["pms.amenity"]
        amenity_type1 = AmenityType.create(
            {
                "name": "TestAmenityType1",
                "pms_property_ids": [
                    (4, self.pms_property1.id),
                    (4, self.pms_property2.id),
                    (4, self.pms_property3.id),
                ],
            }
        )
        # ACT
        Amenity.create(
            {
                "name": "TestAmenity1",
                "pms_amenity_type_id": amenity_type1.id,
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
        # ASSERT
        with self.assertRaises(ValidationError):
            amenity_type1.pms_property_ids = [
                (
                    6,
                    0,
                    [self.pms_property1.id, self.pms_property2.id],
                )
            ]
            amenity_type1.flush()
