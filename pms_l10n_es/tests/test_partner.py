import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import common


@freeze_time("2011-03-16")
class TestResPartner(common.SavepointCase):
    def create_common_scenario(self):
        self.folio_sequence = self.env["ir.sequence"].create(
            {
                "name": "PMS Folio",
                "code": "pms.folio",
                "padding": 4,
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        self.reservation_sequence = self.env["ir.sequence"].create(
            {
                "name": "PMS Reservation",
                "code": "pms.reservation",
                "padding": 4,
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        self.checkin_sequence = self.env["ir.sequence"].create(
            {
                "name": "PMS Checkin",
                "code": "pms.checkin.partner",
                "padding": 4,
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        self.property_test = self.property = self.env["pms.property"].create(
            {
                "name": "My property test",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )

    def test_check_precheckin_state(self):
        # arrange
        self.create_common_scenario()
        today = fields.date.today()
        partner = self.env["res.partner"].create(
            {
                "name": "name1",
                # "lastname": "lastname1",
                "lastname2": "secondlastname",
                "document_expedition_date": "2011-02-20",
                "birthdate_date": "1995-12-10",
                "gender": "male",
                "document_type": "D",
                "document_number": "30065089H",
            }
        )
        reservation_vals = {
            "checkin": today,
            "checkout": today + datetime.timedelta(days=3),
            "partner_id": partner.id,
            "adults": 1,
            "pms_property_id": self.property_test.id,
        }
        # action
        reservation = self.env["pms.reservation"].create(reservation_vals)
        checkin = self.env["pms.checkin.partner"].create(
            {
                "partner_id": partner.id,
                "reservation_id": reservation.id,
            }
        )

        # assert

        self.assertEqual(
            checkin.state, "precheckin", "partner's fields weren't checked"
        )

    def test_error_action_on_board(self):
        # arrange
        self.create_common_scenario()
        today = fields.date.today()
        partner = self.env["res.partner"].create(
            {
                "name": "partner1",
            }
        )
        reservation_vals = {
            "checkin": today,
            "checkout": today + datetime.timedelta(days=3),
            "partner_id": partner.id,
            "adults": 1,
            "pms_property_id": self.property_test.id,
        }
        # action
        reservation = self.env["pms.reservation"].create(reservation_vals)
        checkin = self.env["pms.checkin.partner"].create(
            {
                "partner_id": partner.id,
                "reservation_id": reservation.id,
            }
        )

        # arrange
        with self.assertRaises(ValidationError):
            checkin.action_on_board()

    def test_right_action_on_board(self):
        # arrange
        self.create_common_scenario()
        today = fields.date.today()
        partner = self.env["res.partner"].create(
            {
                "name": "name1",
                # "lastname": "lastname1",
                "lastname2": "secondlastname",
                "document_expedition_date": "2011-02-20",
                "birthdate_date": "1995-12-10",
                "gender": "male",
                "document_type": "D",
                "document_number": "30065089H",
            }
        )
        reservation_vals = {
            "checkin": today,
            "checkout": today + datetime.timedelta(days=3),
            "partner_id": partner.id,
            "adults": 1,
            "pms_property_id": self.property_test.id,
        }
        # action
        reservation = self.env["pms.reservation"].create(reservation_vals)
        checkin = self.env["pms.checkin.partner"].create(
            {
                "partner_id": partner.id,
                "reservation_id": reservation.id,
            }
        )
        checkin.action_on_board()
        # arrange
        self.assertEqual(reservation.state, "onboard", "reservation's state is wrong")
        self.assertEqual(checkin.state, "onboard", "checkin's state is wrong")
