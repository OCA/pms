# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <dev@redneboa.es>
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import datetime
from datetime import timedelta
from odoo import fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import ValidationError
from .common import TestHotel
from odoo.addons.hotel import date_utils
import pytz
import logging
_logger = logging.getLogger(__name__)


class TestHotelReservations(TestHotel):

    def test_create_reservation(self):
        now_utc_dt = date_utils.now()
        reserv_start_utc_dt = now_utc_dt + timedelta(days=3)
        reserv_end_utc_dt = reserv_start_utc_dt + timedelta(days=3)
        folio = self.create_folio(self.user_hotel_manager, self.partner_2)
        reservation = self.create_reservation(
            self.user_hotel_manager,
            folio,
            reserv_start_utc_dt,
            reserv_end_utc_dt,
            self.hotel_room_double_200,
            "Reservation Test #1")

        reserv_start_dt = date_utils.dt_as_timezone(reserv_start_utc_dt,
                                                    self.tz_hotel)
        reserv_end_dt = date_utils.dt_as_timezone(reserv_end_utc_dt -
                                                  timedelta(days=1),
                                                  self.tz_hotel)
        self.assertEqual(reservation.reservation_lines[0].date,
                         reserv_start_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                         "Reservation lines don't start in the correct date")
        self.assertEqual(reservation.reservation_lines[-1].date,
                         reserv_end_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                         "Reservation lines don't end in the correct date")

        total_price = 0.0
        for rline in reservation.reservation_lines:
            total_price += rline.price
        self.assertEqual(folio.amount_untaxed, total_price,
                         "Folio amount doesn't match with reservation lines")

    def test_create_reservations(self):
        now_utc_dt = date_utils.now()
        reserv_start_utc_dt = now_utc_dt + timedelta(days=3)
        reserv_end_utc_dt = reserv_start_utc_dt + timedelta(days=3)
        folio = self.create_folio(self.user_hotel_manager, self.partner_2)
        reservation = self.create_reservation(
            self.user_hotel_manager,
            folio,
            reserv_start_utc_dt,
            reserv_end_utc_dt,
            self.hotel_room_double_200,
            "Reservation Test #1")

        reserv_start_utc_dt = reserv_end_utc_dt
        reserv_end_utc_dt = reserv_start_utc_dt + timedelta(days=3)
        folio = self.create_folio(self.user_hotel_manager, self.partner_2)
        reservation = self.create_reservation(
            self.user_hotel_manager,
            folio,
            reserv_start_utc_dt,
            reserv_end_utc_dt,
            self.hotel_room_double_200,
            "Reservation Test #2")

        reserv_end_utc_dt = now_utc_dt + timedelta(days=3)
        reserv_start_utc_dt = reserv_end_utc_dt - timedelta(days=1)
        folio = self.create_folio(self.user_hotel_manager, self.partner_2)
        reservation = self.create_reservation(
            self.user_hotel_manager,
            folio,
            reserv_start_utc_dt,
            reserv_end_utc_dt,
            self.hotel_room_double_200,
            "Reservation Test #3")

        reserv_start_utc_dt = now_utc_dt + timedelta(days=3)
        reserv_end_utc_dt = reserv_start_utc_dt + timedelta(days=3)
        folio = self.create_folio(self.user_hotel_manager, self.partner_2)
        reservation = self.create_reservation(
            self.user_hotel_manager,
            folio,
            reserv_start_utc_dt,
            reserv_end_utc_dt,
            self.hotel_room_simple_100,
            "Reservation Test #4")

    def test_create_invalid_reservations(self):
        now_utc_dt = date_utils.now()

        org_reserv_start_utc_dt = now_utc_dt + timedelta(days=3)
        org_reserv_end_utc_dt = org_reserv_start_utc_dt + timedelta(days=6)
        folio = self.create_folio(self.user_hotel_manager, self.partner_2)
        reservation = self.create_reservation(
            self.user_hotel_manager,
            folio,
            org_reserv_start_utc_dt,
            org_reserv_end_utc_dt,
            self.hotel_room_double_200,
            "Original Reservation Test #1")

        # Same Dates
        reserv_start_utc_dt = now_utc_dt + timedelta(days=3)
        reserv_end_utc_dt = reserv_start_utc_dt + timedelta(days=6)
        with self.assertRaises(ValidationError):
            folio = self.create_folio(self.user_hotel_manager, self.partner_2)
            reservation = self.create_reservation(
                self.user_hotel_manager,
                folio,
                reserv_start_utc_dt,
                reserv_end_utc_dt,
                self.hotel_room_double_200,
                "Invalid Reservation Test #1")

        # Inside Org Reservation (Start Same Date)
        reserv_start_utc_dt = now_utc_dt + timedelta(days=3)
        reserv_end_utc_dt = reserv_start_utc_dt + timedelta(days=3)
        with self.assertRaises(ValidationError):
            folio = self.create_folio(self.user_hotel_manager, self.partner_2)
            reservation = self.create_reservation(
                self.user_hotel_manager,
                folio,
                reserv_start_utc_dt,
                reserv_end_utc_dt,
                self.hotel_room_double_200,
                "Invalid Reservation Test #2")

        # Inside Org Reservation (Start after)
        reserv_start_utc_dt = now_utc_dt + timedelta(days=4)
        reserv_end_utc_dt = reserv_start_utc_dt + timedelta(days=3)
        with self.assertRaises(ValidationError):
            folio = self.create_folio(self.user_hotel_manager, self.partner_2)
            reservation = self.create_reservation(
                self.user_hotel_manager,
                folio,
                reserv_start_utc_dt,
                reserv_end_utc_dt,
                self.hotel_room_double_200,
                "Invalid Reservation Test #3")

        # Intersect Org Reservation (Start before)
        reserv_start_utc_dt = now_utc_dt + timedelta(days=2)
        reserv_end_utc_dt = reserv_start_utc_dt + timedelta(days=3)
        with self.assertRaises(ValidationError):
            folio = self.create_folio(self.user_hotel_manager, self.partner_2)
            reservation = self.create_reservation(
                self.user_hotel_manager,
                folio,
                reserv_start_utc_dt,
                reserv_end_utc_dt,
                self.hotel_room_double_200,
                "Invalid Reservation Test #4")

        # Intersect Org Reservation (End Same)
        reserv_start_utc_dt = org_reserv_end_utc_dt - timedelta(days=2)
        reserv_end_utc_dt = org_reserv_end_utc_dt
        with self.assertRaises(ValidationError):
            folio = self.create_folio(self.user_hotel_manager, self.partner_2)
            reservation = self.create_reservation(
                self.user_hotel_manager,
                folio,
                reserv_start_utc_dt,
                reserv_end_utc_dt,
                self.hotel_room_double_200,
                "Invalid Reservation Test #5")

        # Intersect Org Reservation (End after)
        reserv_start_utc_dt = org_reserv_end_utc_dt - timedelta(days=2)
        reserv_end_utc_dt = org_reserv_end_utc_dt + timedelta(days=3)
        with self.assertRaises(ValidationError):
            folio = self.create_folio(self.user_hotel_manager, self.partner_2)
            reservation = self.create_reservation(
                self.user_hotel_manager,
                folio,
                reserv_start_utc_dt,
                reserv_end_utc_dt,
                self.hotel_room_double_200,
                "Invalid Reservation Test #6")

        # Overlays Org Reservation
        reserv_start_utc_dt = org_reserv_start_utc_dt - timedelta(days=2)
        reserv_end_utc_dt = org_reserv_end_utc_dt + timedelta(days=2)
        with self.assertRaises(ValidationError):
            folio = self.create_folio(self.user_hotel_manager, self.partner_2)
            reservation = self.create_reservation(
                self.user_hotel_manager,
                folio,
                reserv_start_utc_dt,
                reserv_end_utc_dt,
                self.hotel_room_double_200,
                "Invalid Reservation Test #7")

        # Checkin > Checkout
        with self.assertRaises(ValidationError):
            folio = self.create_folio(self.user_hotel_manager, self.partner_2)
            reservation = self.create_reservation(
                self.user_hotel_manager,
                folio,
                org_reserv_end_utc_dt,
                org_reserv_start_utc_dt,
                self.hotel_room_simple_100,
                "Invalid Reservation Test #8")

    def test_modify_reservation(self):
        now_utc_dt = date_utils.now()

        # 5.0, 15.0, 15.0, 35.0, 35.0, 10.0, 10.0

        room_type_prices = self.prices_tmp[self.hotel_room_double_200.price_room_type.id]
        org_reserv_start_utc_dt = now_utc_dt + timedelta(days=1)
        org_reserv_end_utc_dt = org_reserv_start_utc_dt + timedelta(days=2)
        folio = self.create_folio(self.user_hotel_manager, self.partner_2)
        reservation = self.create_reservation(
            self.user_hotel_manager,
            folio,
            org_reserv_start_utc_dt,
            org_reserv_end_utc_dt,
            self.hotel_room_double_200,
            "Original Reservation Test #1")
        ndate = org_reserv_start_utc_dt
        for r_k, r_v in enumerate(reservation.reservation_lines):
            self.assertEqual(r_v.date, ndate.strftime(DEFAULT_SERVER_DATE_FORMAT))
            self.assertEqual(r_v.price, room_type_prices[r_k+1])
            ndate = ndate + timedelta(days=1)
        self.assertEqual(reservation.amount_room, 30.0)
        ndate = org_reserv_start_utc_dt + timedelta(days=1)
        line = reservation.reservation_lines.filtered(lambda r: r.date == ndate.strftime(DEFAULT_SERVER_DATE_FORMAT))
        reservation.reservation_lines = [(1, line.id, {'price': 100.0})]
        self.assertEqual(reservation.amount_room, 115.0)
        reservation.sudo(self.user_hotel_manager).write({
            'checkin': (org_reserv_start_utc_dt + timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT),
            'checkout': (org_reserv_end_utc_dt + timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT),
        })
        self.assertEqual(reservation.amount_room, 135.0)
