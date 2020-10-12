from datetime import timedelta

from odoo import fields

from .common import TestHotel


class TestPmsReservations(TestHotel):
    def test_create_reservation(self):
        today = fields.date.today()
        checkin = today + timedelta(days=8)
        checkout = checkin + timedelta(days=11)
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
            checkout - timedelta(1),
            "Reservation lines don't end in the correct date",
        )
