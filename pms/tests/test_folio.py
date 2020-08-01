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
from datetime import timedelta

from odoo.addons.hotel import date_utils

from .common import TestHotel


class TestHotelReservations(TestHotel):
    def test_cancel_folio(self):
        now_utc_dt = date_utils.now()

        org_reserv_start_utc_dt = now_utc_dt + timedelta(days=3)
        org_reserv_end_utc_dt = org_reserv_start_utc_dt + timedelta(days=6)
        folio = self.create_folio(self.user_hotel_manager, self.partner_2)
        reservation_a = self.create_reservation(
            self.user_hotel_manager,
            folio,
            org_reserv_start_utc_dt,
            org_reserv_end_utc_dt,
            self.hotel_room_double_200,
            "Reservation Test #1",
        )
        reservation_b = self.create_reservation(
            self.user_hotel_manager,
            folio,
            org_reserv_start_utc_dt,
            org_reserv_end_utc_dt,
            self.hotel_room_simple_100,
            "Reservation Test #2",
        )
        self.assertEqual(len(folio.reservation_ids), 2, "Invalid room lines count")
        folio.action_cancel()
        self.assertEqual(folio.state, "cancel", "Invalid folio state")
        for rline in folio.reservation_ids:
            self.assertEqual(rline.state, "cancelled", "Invalid reservation state")
