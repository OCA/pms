import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import common


@freeze_time("2011-03-16")
class TestResPartner(common.SavepointCase):
    def test_check_precheckin_state(self):
        # arrange
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
        today = fields.date.today()
        # arrange
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
        # arrange
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
