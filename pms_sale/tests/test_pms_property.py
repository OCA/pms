# Copyright (c) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests import SavepointCase


class TestPMSProperty(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env.ref("pms_sale.product_product_reservation")
        cls.partner_owner = cls.env["res.partner"].create({"name": "Property Owner"})
        cls.partner_property = cls.env["res.partner"].create({"name": "Property"})
        cls.property = cls.env["pms.property"].create(
            {"owner_id": cls.partner_owner.id, "partner_id": cls.partner_property.id}
        )
        cls.partner_owner_2 = cls.env["res.partner"].create(
            {"name": "Property Owner 2"}
        )
        cls.partner_property_2 = cls.env["res.partner"].create({"name": "Property 2"})
        cls.property_2 = cls.env["pms.property"].create(
            {
                "owner_id": cls.partner_owner.id,
                "partner_id": cls.partner_property_2.id,
                "max_nights": 21,
            }
        )

        cls.my_pms_property_reservation = cls.env["pms.property.reservation"].create(
            {
                "name": "PMS property reservation 1",
                "product_id": cls.product.id,
                "property_id": cls.property.id,
            }
        )
        cls.my_pms_property_reservation_2 = cls.env["pms.property.reservation"].create(
            {
                "name": "PMS property reservation 2",
                "product_id": cls.product.id,
                "property_id": cls.property.id,
            }
        )

        cls.pms_property2 = cls.env["pms.property"].create(
            {
                "name": "Property_2",
                "ref": "test ref",
                "owner_id": cls.partner_owner.id,
                "city": "la",
                "room_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Room 101",
                            "type_id": 7,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Room 102",
                            "type_id": 7,
                        },
                    ),
                ],
                "property_child_ids": [],
                "reservation_ids": [
                    (
                        0,
                        0,
                        {
                            "name": cls.my_pms_property_reservation.name,
                            "product_id": cls.product.id,
                            "property_id": cls.property.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": cls.my_pms_property_reservation_2.name,
                            "product_id": cls.product.id,
                            "property_id": cls.property.id,
                        },
                    ),
                ],
            }
        )

        cls.reservation = cls.env["pms.reservation"].create(
            {
                "name": "Test Reservation",
                "property_id": cls.property_2.id,
                "start": "2022-06-01",
                "stop": "2022-06-15",
            }
        )

    def test_get_property_information(self):
        vals = {
            "city_value": "la",
            "bedrooms_value": 2,
            "datepicker_value": "12/1/2022-12/15/2022",
        }

        self.assertEqual(len(self.pms_property2.get_property_information(vals)), 1)
