from odoo.exceptions import ValidationError

from .common import TestHotel


class TestPmsAmenity(TestHotel):
    def create_common_scenario(self):
        # create company and properties
        self.company1 = self.env["res.company"].create(
            {
                "name": "Pms_Company_Test",
            }
        )
        self.property1 = self.env["pms.property"].create(
            {
                "name": "Pms_property_test1",
                "company_id": self.company1.id,
                "default_pricelist_id": self.env.ref("product.list0").id,
            }
        )
        self.property2 = self.env["pms.property"].create(
            {
                "name": "Pms_property_test2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.env.ref("product.list0").id,
            }
        )

        self.property3 = self.env["pms.property"].create(
            {
                "name": "Pms_property_test3",
                "company_id": self.company1.id,
                "default_pricelist_id": self.env.ref("product.list0").id,
            }
        )

    def test_property_not_allowed(self):
        # ARRANGE
        name = "amenityTest1"
        name2 = "amenity"
        self.create_common_scenario()
        AmenityType = self.env["pms.amenity.type"]
        Amenity = self.env["pms.amenity"]
        # ACT
        A1 = AmenityType.create(
            {
                "name": name,
                "pms_property_ids": [
                    (4, self.property1.id),
                    (4, self.property2.id),
                ],
            }
        )
        # ASSERT
        with self.assertRaises(ValidationError), self.cr.savepoint():
            Amenity.create(
                {
                    "name": name2,
                    "room_amenity_type_id": A1.id,
                    "pms_property_ids": [
                        (4, self.property1.id),
                        (4, self.property2.id),
                        (4, self.property3.id),
                    ],
                }
            )

    def test_check_allowed_property_ids(self):
        # ARRANGE
        name = "amenityTest1"
        name2 = "amenity"
        self.create_common_scenario()
        AmenityType = self.env["pms.amenity.type"]
        Amenity = self.env["pms.amenity"]
        # ACT
        AT1 = AmenityType.create(
            {
                "name": name,
                "pms_property_ids": [
                    (4, self.property1.id),
                    (4, self.property2.id),
                ],
            }
        )
        A2 = Amenity.create(
            {
                "name": name2,
                "room_amenity_type_id": AT1.id,
                "pms_property_ids": [
                    (4, self.property1.id),
                    (4, self.property2.id),
                ],
            }
        )
        # ASSERT
        self.assertEqual(
            A2.allowed_property_ids, AT1.pms_property_ids, "Properties doesnt much"
        )
