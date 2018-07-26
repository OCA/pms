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
from openerp.tools import (
    DEFAULT_SERVER_DATETIME_FORMAT,
    DEFAULT_SERVER_DATE_FORMAT)
from odoo.addons.hotel import date_utils
from .common import TestHotelWubook


class TestHotelFolio(TestHotelWubook):

    def test_has_wubook_reservations(self):
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
                self.hotel_vroom_budget.wrid: {
                    'occupancy': [1],
                    'dayprices': [15.0, 15.0]
                }
            }
        )]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertTrue(any(processed_rids), "Reservation not found")
        self.assertFalse(errors, "Reservation errors")
        nreserv = self.env['hotel.reservation'].search([
            ('wrid', '=', processed_rids[0])
        ], order='id ASC', limit=1)
        self.assertTrue(nreserv, "Can't found reservation")
        self.assertTrue(nreserv.folio_id.whas_wubook_reservations,
                        "Can't found reservations from wubook")

    def test_import_reservations(self):
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
                self.hotel_vroom_budget.wrid: {
                    'occupancy': [1],
                    'dayprices': [15.0, 15.0]
                }
            }
        )]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertTrue(any(processed_rids), "Reservation not found")
        self.assertFalse(errors, "Reservation errors")
        nreserv = self.env['hotel.reservation'].search([
            ('wrid', '=', processed_rids[0])
        ], order='id ASC', limit=1)
        self.assertTrue(nreserv, "Can't found reservation")
        nreserv.folio_id.import_reservations()

    def test_action_confirm(self):
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
                self.hotel_vroom_budget.wrid: {
                    'occupancy': [1],
                    'dayprices': [15.0, 15.0]
                }
            }
        )]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertTrue(any(processed_rids), "Reservation not found")
        self.assertFalse(errors, "Reservation errors")
        nreserv = self.env['hotel.reservation'].search([
            ('wrid', '=', processed_rids[0])
        ], order='id ASC', limit=1)
        self.assertTrue(nreserv, "Can't found reservation")
        nreserv.folio_id.action_confirm()
        self.assertEqual(nreserv.folio_id.state,
                         'sale',
                         "Reservation not confirmed")
