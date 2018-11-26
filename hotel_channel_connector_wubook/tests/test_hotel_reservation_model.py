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
from datetime import timedelta
from openerp.exceptions import UserError
from openerp.tools import (
    DEFAULT_SERVER_DATETIME_FORMAT,
    DEFAULT_SERVER_DATE_FORMAT)
from odoo.addons.hotel import date_utils
from .common import TestHotelWubook


class TestHotelReservation(TestHotelWubook):

    def test_is_from_ota(self):
        now_utc_dt = date_utils.now()
        checkin_utc_dt = now_utc_dt + timedelta(days=3)
        checkin_dt = date_utils.dt_as_timezone(checkin_utc_dt,
                                               self.tz_hotel)
        checkout_utc_dt = checkin_utc_dt + timedelta(days=2)
        date_diff = date_utils.date_diff(checkin_utc_dt, checkout_utc_dt,
                                         hours=False) + 1

        wbooks = [self.create_wubook_booking(
            self.user_hotel_manager,
            checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            self.partner_2,
            {
                self.hotel_room_type_budget.wrid: {
                    'occupancy': [1],   # 1 Reservation Line
                    'dayprices': [15.0, 15.0]   # 2 Days
                }
            },
            channel=self.wubook_channel_test.wid,
        )]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)

        # Check Creation
        self.assertTrue(any(processed_rids), "Reservation not found")
        self.assertFalse(errors, "Reservation errors")

        hotel_reserv_obj = self.env['hotel.reservation']
        nreserv = hotel_reserv_obj.sudo(self.user_hotel_manager).search([
            ('wrid', 'in', processed_rids)
        ])
        self.assertTrue(nreserv, "Reservation not found")
        self.assertTrue(nreserv.is_from_ota)
        nreserv.wrid = ''
        self.assertFalse(nreserv.is_from_ota)

    def test_write(self):
        now_utc_dt = date_utils.now()
        checkin_utc_dt = now_utc_dt + timedelta(days=3)
        checkin_dt = date_utils.dt_as_timezone(checkin_utc_dt,
                                               self.tz_hotel)
        checkout_utc_dt = checkin_utc_dt + timedelta(days=2)
        date_diff = date_utils.date_diff(checkin_utc_dt, checkout_utc_dt,
                                         hours=False) + 1

        wbooks = [self.create_wubook_booking(
            self.user_hotel_manager,
            checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            self.partner_2,
            {
                self.hotel_room_type_budget.wrid: {
                    'occupancy': [1],   # 1 Reservation Line
                    'dayprices': [15.0, 15.0]   # 2 Days
                }
            }
        )]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)

        # Check Creation
        self.assertTrue(any(processed_rids), "Reservation not found")
        self.assertFalse(errors, "Reservation errors")

        hotel_reserv_obj = self.env['hotel.reservation']
        nreserv = hotel_reserv_obj.sudo(self.user_hotel_manager).search([
            ('wrid', 'in', processed_rids)
        ])
        self.assertTrue(nreserv, "Reservation not found")
        checkin_utc_dt = now_utc_dt + timedelta(days=6)
        checkout_utc_dt = checkin_utc_dt + timedelta(days=2)
        nreserv.write({
            'checkin': checkin_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'checkout': checkout_utc_dt.strftime(
                                            DEFAULT_SERVER_DATETIME_FORMAT),
        })

    def test_unlink(self):
        now_utc_dt = date_utils.now()
        checkin_utc_dt = now_utc_dt + timedelta(days=3)
        checkin_dt = date_utils.dt_as_timezone(checkin_utc_dt,
                                               self.tz_hotel)
        checkout_utc_dt = checkin_utc_dt + timedelta(days=2)
        date_diff = date_utils.date_diff(checkin_utc_dt, checkout_utc_dt,
                                         hours=False) + 1

        wbooks = [self.create_wubook_booking(
            self.user_hotel_manager,
            checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            self.partner_2,
            {
                self.hotel_room_type_budget.wrid: {
                    'occupancy': [1],   # 1 Reservation Line
                    'dayprices': [15.0, 15.0]   # 2 Days
                }
            }
        )]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)

        # Check Creation
        self.assertTrue(any(processed_rids), "Reservation not found")
        self.assertFalse(errors, "Reservation errors")

        hotel_reserv_obj = self.env['hotel.reservation']
        nreserv = hotel_reserv_obj.sudo(self.user_hotel_manager).search([
            ('wrid', 'in', processed_rids)
        ])
        self.assertTrue(nreserv, "Reservation not found")

        with self.assertRaises(UserError):
            nreserv.sudo(self.user_hotel_manager).unlink()

    def test_action_cancel(self):
        now_utc_dt = date_utils.now()
        checkin_utc_dt = now_utc_dt + timedelta(days=3)
        checkin_dt = date_utils.dt_as_timezone(checkin_utc_dt,
                                               self.tz_hotel)
        checkout_utc_dt = checkin_utc_dt + timedelta(days=2)
        date_diff = date_utils.date_diff(checkin_utc_dt, checkout_utc_dt,
                                         hours=False) + 1

        wbooks = [self.create_wubook_booking(
            self.user_hotel_manager,
            checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            self.partner_2,
            {
                self.hotel_room_type_budget.wrid: {
                    'occupancy': [1],   # 1 Reservation Line
                    'dayprices': [15.0, 15.0]   # 2 Days
                }
            }
        )]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)

        # Check Creation
        self.assertTrue(any(processed_rids), "Reservation not found")
        self.assertFalse(errors, "Reservation errors")

        hotel_reserv_obj = self.env['hotel.reservation']
        nreserv = hotel_reserv_obj.sudo(self.user_hotel_manager).search([
            ('wrid', 'in', processed_rids)
        ])
        self.assertTrue(nreserv, "Reservation not found")
        nreserv.sudo(self.user_hotel_manager).action_cancel()
        self.assertEqual(nreserv.state, 'cancelled',
                         "Rervation don't cancelled")
