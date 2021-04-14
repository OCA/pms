from odoo.exceptions import ValidationError
from odoo.tests import common


class TestPmsResUser(common.SavepointCase):
    def create_common_scenario(self):
        # create a room type availability
        self.room_type_availability = self.env["pms.availability.plan"].create(
            {"name": "Availability plan 1"}
        )

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
        self.folio_sequenceA = self.env["ir.sequence"].create(
            {
                "name": "PMS Folio",
                "code": "pms.folio",
                "padding": 4,
                "company_id": self.company_A.id,
            }
        )
        self.reservation_sequenceA = self.env["ir.sequence"].create(
            {
                "name": "PMS Reservation",
                "code": "pms.reservation",
                "padding": 4,
                "company_id": self.company_A.id,
            }
        )
        self.checkin_sequenceA = self.env["ir.sequence"].create(
            {
                "name": "PMS Checkin",
                "code": "pms.checkin.partner",
                "padding": 4,
                "company_id": self.company_A.id,
            }
        )
        self.folio_sequenceB = self.env["ir.sequence"].create(
            {
                "name": "PMS Folio",
                "code": "pms.folio",
                "padding": 4,
                "company_id": self.company_B.id,
            }
        )
        self.reservation_sequenceB = self.env["ir.sequence"].create(
            {
                "name": "PMS Reservation",
                "code": "pms.reservation",
                "padding": 4,
                "company_id": self.company_B.id,
            }
        )
        self.checkin_sequenceB = self.env["ir.sequence"].create(
            {
                "name": "PMS Checkin",
                "code": "pms.checkin.partner",
                "padding": 4,
                "company_id": self.company_B.id,
            }
        )
        self.property_A1 = self.env["pms.property"].create(
            {
                "name": "Pms_property",
                "company_id": self.company_A.id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "folio_sequence_id": self.folio_sequenceA.id,
                "reservation_sequence_id": self.reservation_sequenceA.id,
                "checkin_sequence_id": self.checkin_sequenceA.id,
            }
        )
        self.property_A2 = self.env["pms.property"].create(
            {
                "name": "Pms_property2",
                "company_id": self.company_A.id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "folio_sequence_id": self.folio_sequenceA.id,
                "reservation_sequence_id": self.reservation_sequenceA.id,
                "checkin_sequence_id": self.checkin_sequenceA.id,
            }
        )
        self.property_B1 = self.env["pms.property"].create(
            {
                "name": "Pms_propertyB1",
                "company_id": self.company_B.id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "folio_sequence_id": self.folio_sequenceB.id,
                "reservation_sequence_id": self.reservation_sequenceB.id,
                "checkin_sequence_id": self.checkin_sequenceB.id,
            }
        )

    def test_property_not_allowed(self):
        """
        Property not allowed, it belongs to another company

        Company_A ---> Property_A1, Property_A2
        Company_B ---> Property_B1

        """
        # ARRANGE
        name = "test user"
        login = "test_user"
        self.create_common_scenario()
        Users = self.env["res.users"]
        # ACT & ASSERT
        with self.assertRaises(ValidationError), self.cr.savepoint():
            Users.create(
                {
                    "name": name,
                    "login": login,
                    "company_ids": [(4, self.company_A.id)],
                    "company_id": self.company_A.id,
                    "pms_property_ids": [(4, self.property_A1.id)],
                    "pms_property_id": self.property_B1.id,
                }
            )

    def test_check_allowed_property_ids(self):
        # ARRANGE
        name = "test user2"
        login = "test_user2"
        self.create_common_scenario()
        Users = self.env["res.users"]
        # ACT & ASSERT
        with self.assertRaises(ValidationError), self.cr.savepoint():
            Users.create(
                {
                    "name": name,
                    "login": login,
                    "company_ids": [(4, self.company_A.id)],
                    "company_id": self.company_A.id,
                    "pms_property_ids": [
                        (4, self.property_A1.id),
                        (4, self.property_B1.id),
                    ],
                    "pms_property_id": self.property_A1.id,
                }
            )
