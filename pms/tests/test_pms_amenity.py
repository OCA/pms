from odoo.exceptions import UserError

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
        with self.assertRaises(UserError), self.cr.savepoint():
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
