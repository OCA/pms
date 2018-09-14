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
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.hotel import date_utils
from .common import TestHotelWubook
import logging
_logger = logging.getLogger(__name__)


class TestResPartner(TestHotelWubook):

    def test_write(self):
        now_utc_dt = date_utils.now()
        checkin_utc_dt = now_utc_dt + timedelta(days=3)
        checkin_dt = date_utils.dt_as_timezone(checkin_utc_dt,
                                               self.tz_hotel)
        checkout_utc_dt = checkin_utc_dt + timedelta(days=2)
        date_diff = date_utils.date_diff(checkin_utc_dt, checkout_utc_dt,
                                         hours=False) + 1

        wbooks = [
            self.create_wubook_booking(
                self.user_hotel_manager,
                checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                self.partner_2,
                {
                    self.hotel_room_type_budget.wrid: {
                        'occupancy': [1],
                        'dayprices': [15.0, 15.0]
                    }
                }
            ),
            self.create_wubook_booking(
                self.user_hotel_manager,
                checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                self.partner_1,
                {
                    self.hotel_room_type_budget.wrid: {
                        'occupancy': [1],
                        'dayprices': [15.0, 15.0]
                    }
                }
            )
        ]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertTrue(any(processed_rids), "Reservation not found")
        self.assertFalse(errors, "Reservation errors")
        self.partner_2.sudo(self.user_hotel_manager).write({
            'vat': 'ES00000000T'
        })
        self.partner_1.sudo(self.user_hotel_manager).write({
            'vat': 'ES00000000T',
            'unconfirmed': True,
        })
        reservation = self.env['hotel.reservation'].search([
            ('wrid', '=', processed_rids[1])
        ], order='id ASC', limit=1)
        self.assertTrue(reservation, "Can't found reservation")
        self.assertFalse(self.partner_1.active, "Uncofirmed user still active")
        self.assertEqual(reservation.partner_id.id,
                         self.partner_2.id,
                         "Old Partner not changed")
