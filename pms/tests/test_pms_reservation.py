import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import ValidationError

from .common import TestHotel


@freeze_time("2012-01-14")
class TestPmsReservations(TestHotel):
    def test_create_reservation(self):
        today = fields.date.today()
        checkin = today + datetime.timedelta(days=8)
        checkout = checkin + datetime.timedelta(days=11)
        demo_user = self.env.ref("base.user_demo")
        customer = self.env.ref("base.res_partner_12")
        reservation_vals = {
            "checkin": checkin,
            "checkout": checkout,
            "room_type_id": self.room_type_3.id,
            "partner_id": customer.id,
            "pms_property_id": self.main_hotel_property.id,
        }
        reservation = (
            self.env["pms.reservation"].with_user(demo_user).create(reservation_vals)
        )

        self.assertEqual(
            reservation.reservation_line_ids[0].date,
            checkin,
            "Reservation lines don't start in the correct date",
        )
        self.assertEqual(
            reservation.reservation_line_ids[-1].date,
            checkout - datetime.timedelta(1),
            "Reservation lines don't end in the correct date",
        )

    def test_manage_children_raise(self):

        # ARRANGE
        PmsReservation = self.env["pms.reservation"]

        # ACT & ASSERT
        with self.assertRaises(ValidationError), self.cr.savepoint():

            PmsReservation.create(
                {
                    "adults": 2,
                    "children_occupying": 1,
                    "checkin": datetime.datetime.now(),
                    "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                    "room_type_id": self.browse_ref("pms.pms_room_type_0").id,
                }
            )
