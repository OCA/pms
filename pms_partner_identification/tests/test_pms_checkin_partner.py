from datetime import date, timedelta

from odoo.exceptions import ValidationError

from odoo.addons.pms.tests.common import TestPms


class TestPmsCheckinPartner(TestPms):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        today = date(2012, 1, 14)
        cls.room_type1 = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id],
                "name": "Triple",
                "default_code": "TRP",
                "class_id": cls.room_type_class1.id,
            }
        )
        cls.room1 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Triple 101",
                "room_type_id": cls.room_type1.id,
                "capacity": 3,
            }
        )
        cls.room1_2 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Triple 111",
                "room_type_id": cls.room_type1.id,
                "capacity": 3,
            }
        )
        cls.room1_3 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Triple 222",
                "room_type_id": cls.room_type1.id,
                "capacity": 3,
            }
        )

        cls.host1 = cls.env["res.partner"].create(
            {
                "name": "Miguel",
                "email": "miguel@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        cls.sale_channel_direct1 = cls.env["pms.sale.channel"].create(
            {
                "name": "Door",
                "channel_type": "direct",
            }
        )
        reservation_vals = {
            "checkin": today,
            "checkout": today + timedelta(days=3),
            "room_type_id": cls.room_type1.id,
            "partner_id": cls.host1.id,
            "adults": 3,
            "pms_property_id": cls.pms_property1.id,
            "sale_channel_origin_id": cls.sale_channel_direct1.id,
        }
        cls.reservation_1 = cls.env["pms.reservation"].create(reservation_vals)
        cls.checkin1 = cls.env["pms.checkin.partner"].create(
            {
                "partner_id": cls.host1.id,
                "reservation_id": cls.reservation_1.id,
            }
        )
        cls.country = cls.env.ref("base.us")
        cls.doc_type = cls.env["res.partner.id_category"].create(
            {"name": "Test Doc Type", "code": "TDT"}
        )
        cls.checkin1.write(
            {
                "document_number": "12345",
                "document_type": cls.doc_type.id,
                "document_expedition_date": "2023-01-01",
                "document_country_id": cls.country.id,
            }
        )

    def test_add_partner_if_exists_from_checkin(self):
        """
        Check when a document_type and document_number are entered in a checkin if this
        document already existes and is associated with a partner, this partner will be
        associated with the checkin
        """
        # ACT
        host = self.env["res.partner"].create(
            {
                "name": "Ricardo",
                "mobile": "666555666",
                "email": "ricardo@example.com",
                "birthdate_date": "1995-11-14",
                "gender": "male",
            }
        )

        self.env["res.partner.id_number"].create(
            {
                "category_id": self.doc_type.id,
                "name": "55562998N",
                "partner_id": host.id,
            }
        )
        # ARRANGE
        checkin = self.env["pms.checkin.partner"].create(
            {
                "reservation_id": self.reservation_1.id,
                "document_number": "55562998N",
                "document_type": self.doc_type.id,
            }
        )

        # ASSERT
        self.assertEqual(
            checkin.partner_id.id,
            host.id,
            "Checkin partner_id must be the same as the one who has that document",
        )

    def test_compute_document_data(self):
        """Test document data is computed from partner"""
        self.env["res.partner.id_number"].create(
            {
                "name": "67890",
                "category_id": self.doc_type.id,
                "partner_id": self.host1.id,
                "valid_from": "2023-02-01",
                "country_id": self.country.id,
            }
        )

        new_checkin = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.host1.id,
                "reservation_id": self.reservation_1.id,
            }
        )
        new_checkin._compute_partner_document_data()

        self.assertEqual(new_checkin.document_number, "67890")
        self.assertEqual(new_checkin.document_type.id, self.doc_type.id)

    def test_document_country_constraint(self):
        """Test document type and country consistency"""
        self.doc_type.country_ids = self.country
        other_country = self.env["res.country"].create(
            {"name": "Other Country", "code": "OC"}
        )

        with self.assertRaises(ValidationError):
            self.checkin1.document_country_id = other_country

    def test_create_or_update_partner_document(self):
        """Test creation and update of partner documents"""
        self.checkin1._create_or_update_partner_document()

        doc = self.env["res.partner.id_number"].search(
            [("partner_id", "=", self.host1.id), ("name", "=", "12345")]
        )
        self.assertTrue(doc)
        self.assertEqual(doc.category_id, self.doc_type)
        found_partner = self.checkin1._get_partner_by_document("12345", self.doc_type)
        self.assertEqual(found_partner, self.host1)
