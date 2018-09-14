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
from datetime import datetime, timedelta
from openerp.tools import (
    DEFAULT_SERVER_DATETIME_FORMAT,
    DEFAULT_SERVER_DATE_FORMAT)
from odoo.addons.hotel_wubook_proto.wubook import DEFAULT_WUBOOK_DATE_FORMAT
from openerp.exceptions import ValidationError
from .common import TestHotelWubook
from odoo.addons.hotel import date_utils
import pytz
import logging
_logger = logging.getLogger(__name__)


class TestWubook(TestHotelWubook):

    def test_simple_booking(self):
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
        nreserv = self.env['hotel.reservation'].search([
            ('wrid', 'in', processed_rids)
        ], order='id ASC')
        self.assertTrue(nreserv, "Reservation not found")
        self.assertEqual(nreserv.state, 'draft', "Invalid reservation state")
        nfolio = self.env['hotel.folio'].search([
            ('id', '=', nreserv.folio_id.id)
        ], limit=1)
        self.assertTrue(nfolio, "Folio not found")
        self.assertEqual(nfolio.state, 'draft', "Invalid folio state")

        # Check Dates
        self.assertEqual(
            nreserv.checkin,
            checkin_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            "Invalid Checkin Reservation Date")
        self.assertEqual(
            nreserv.checkout,
            checkout_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            "Invalid Checkout Reservation Date")
        # Check Price
        self.assertEqual(nreserv.price_unit, 30.0, "Invalid Reservation Price")
        # Check Reservation Lines
        self.assertTrue(any(nreserv.reservation_line_ids),
                        "Reservation lines snot found")
        dates_arr = date_utils.generate_dates_list(checkin_dt, date_diff-1)
        for k_line, v_line in enumerate(nreserv.reservation_line_ids):
            self.assertEqual(dates_arr[k_line], v_line['date'],
                             "Invalid Reservation Lines Dates")

    def test_complex_booking(self):
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
                    'occupancy': [1, 1],   # 2 Reservation Line
                    'dayprices': [15.0, 15.0]   # 2 Days
                }
            }
        )]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)

        # Check Creation
        self.assertTrue(any(processed_rids), "Reservation not found")
        self.assertFalse(errors, "Reservation errors")
        nreservs = self.env['hotel.reservation'].search([
            ('wrid', 'in', processed_rids)
        ], order='id ASC')
        self.assertEqual(len(nreservs), 2, "Reservations not found")

        for nreserv in nreservs:
            # Check State
            self.assertEqual(nreserv.state, 'draft',
                             "Invalid reservation state")

            # Check Dates
            self.assertEqual(
                nreserv.checkin,
                checkin_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "Invalid Checkin Reservation Date")
            self.assertEqual(
                nreserv.checkout,
                checkout_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "Invalid Checkout Reservation Date")
            # Check Price
            self.assertEqual(nreserv.price_unit, 30.0,
                             "Invalid Reservation Price")
            # Check Reservation Lines
            self.assertTrue(any(nreserv.reservation_line_ids),
                            "Reservation lines snot found")
            dates_arr = date_utils.generate_dates_list(checkin_dt, date_diff-1)
            for k_line, v_line in enumerate(nreserv.reservation_line_ids):
                self.assertEqual(dates_arr[k_line], v_line['date'],
                                 "Invalid Reservation Lines Dates")

    def test_complex_bookings(self):
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
                    self.hotel_room_type_special.wrid: {
                        'occupancy': [2],   # 2 Reservation Line
                        'dayprices': [15.0, 15.0]   # 2 Days
                    }
                }
            ),
            self.create_wubook_booking(
                self.user_hotel_manager,
                (checkin_dt - timedelta(days=3)).strftime(
                                            DEFAULT_SERVER_DATETIME_FORMAT),
                self.partner_2,
                {
                    self.hotel_room_type_special.wrid: {
                        'occupancy': [2],   # 2 Reservation Line
                        'dayprices': [15.0, 15.0]   # 2 Days
                    }
                }
            ),
            self.create_wubook_booking(
                self.user_hotel_manager,
                (checkin_dt + timedelta(days=3)).strftime(
                                            DEFAULT_SERVER_DATETIME_FORMAT),
                self.partner_2,
                {
                    self.hotel_room_type_special.wrid: {
                        'occupancy': [2],   # 2 Reservation Line
                        'dayprices': [15.0, 15.0]   # 2 Days
                    }
                }
            )
        ]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertEqual(len(processed_rids), 3, "Reservation not found")
        self.assertFalse(errors, "Reservation errors")

    def test_cancel_booking(self):
        now_utc_dt = date_utils.now()
        checkin_utc_dt = now_utc_dt + timedelta(days=3)
        checkin_dt = date_utils.dt_as_timezone(checkin_utc_dt,
                                               self.tz_hotel)
        checkout_utc_dt = checkin_utc_dt + timedelta(days=2)
        date_diff = date_utils.date_diff(checkin_utc_dt, checkout_utc_dt,
                                         hours=False) + 1

        def check_state(wrids, state):
            reservs = self.env['hotel.reservation'].sudo().search([
                    ('wrid', 'in', wrids)
                ])
            self.assertTrue(any(reservs), "Reservations not found")
            for reserv in reservs:
                self.assertEqual(
                        reserv.state, state, "Reservation state invalid")

        # Create Reservation
        nbook = self.create_wubook_booking(
            self.user_hotel_manager,
            checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            self.partner_2,
            {
                self.hotel_room_type_special.wrid: {
                    'occupancy': [2],   # 2 Reservation Line
                    'dayprices': [15.0, 15.0]   # 2 Days
                }
            }, channel=self.wubook_channel_test.wid)
        wbooks = [nbook]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertEqual(len(processed_rids), 1, "Reservation not found")
        self.assertFalse(errors, "Reservation errors")

        # Cancel It
        wbooks = [self.cancel_booking(nbook)]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertEqual(len(processed_rids), 1, "Reservation not found")
        self.assertFalse(errors, "Reservation errors")
        check_state(processed_rids, 'cancelled')
        # Can't confirm cancelled bookings
        reserv = self.env['hotel.reservation'].sudo().search([
            ('wrid', 'in', processed_rids)
        ], limit=1)
        with self.assertRaises(ValidationError):
            reserv.confirm()

        # Create Reservation and Cancel It
        nbook = self.create_wubook_booking(
            self.user_hotel_manager,
            checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            self.partner_2,
            {
                self.hotel_room_type_special.wrid: {
                    'occupancy': [2],   # 2 Reservation Line
                    'dayprices': [15.0, 15.0]   # 2 Days
                }
            })
        cbook = self.cancel_booking(nbook)
        wbooks = [nbook, cbook]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertEqual(len(processed_rids), 2, "Reservation not found")
        self.assertFalse(errors, "Reservation errors")
        check_state(processed_rids, 'cancelled')

    def test_splitted_booking(self):
        now_utc_dt = date_utils.now()
        checkin_utc_dt = now_utc_dt + timedelta(days=3)
        checkin_dt = date_utils.dt_as_timezone(checkin_utc_dt,
                                               self.tz_hotel)
        checkout_utc_dt = checkin_utc_dt + timedelta(days=2)
        date_diff = date_utils.date_diff(checkin_utc_dt, checkout_utc_dt,
                                         hours=False) + 1

        book_a = self.create_wubook_booking(
            self.user_hotel_manager,
            checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            self.partner_2,
            {
                self.hotel_room_type_budget.wrid: {
                    'occupancy': [1],
                    'dayprices': [15.0, 15.0]
                }
            }
        )
        book_b = self.create_wubook_booking(
            self.user_hotel_manager,
            (checkin_dt + timedelta(days=2)).strftime(
                                        DEFAULT_SERVER_DATETIME_FORMAT),
            self.partner_2,
            {
                self.hotel_room_type_budget.wrid: {
                    'occupancy': [1],
                    'dayprices': [15.0, 15.0]
                }
            }
        )
        wbooks = [book_a, book_b]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertEqual(len(processed_rids), 2, "Reservation not found")
        self.assertFalse(errors, "Reservation errors")
        reserv = self.env['hotel.reservation'].search([
            ('wrid', '=', book_b['reservation_code'])
        ], order='id ASC', limit=1)
        self.assertTrue(reserv, "Rervation doesn't exists")
        self.assertEqual(
            reserv.product_id.id,
            self.hotel_room_simple_100.product_id.id,
            "Unexpected room assigned")
        reserv.product_id = \
            self.hotel_room_simple_101.product_id.id

        wbooks = [
            self.create_wubook_booking(
                self.user_hotel_manager,
                checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                self.partner_2,
                {
                    self.hotel_room_type_budget.wrid: {
                        'occupancy': [1],
                        'dayprices': [15.0, 15.0, 20.0, 17.0]
                    }
                }
            )
        ]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertEqual(len(processed_rids), 1, "Reservation not found")
        self.assertFalse(errors, "Reservation errors")

        # Check Splitted Integrity
        nreservs = self.env['hotel.reservation'].search([
            ('wrid', 'in', processed_rids)
        ], order="id ASC")
        _logger.info(nreservs)
        self.assertEqual(len(nreservs), 2, "Reservations not found")
        date_dt = date_utils.get_datetime(nreservs[0].checkin)
        self.assertEqual(nreservs[0].reservation_line_ids[0].date,
                         date_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                         "Invalid split")
        date_dt = date_utils.get_datetime(nreservs[1].checkin)
        self.assertEqual(nreservs[1].reservation_line_ids[0].date,
                         date_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                         "Invalid split")
        self.assertEqual(nreservs[0].price_unit,
                         30.0,
                         "Invalid split price")
        self.assertEqual(nreservs[1].price_unit,
                         37.0,
                         "Invalid split price")
        self.assertEqual(nreservs[1].parent_reservation.id,
                         nreservs[0].id,
                         "Invalid split parent reservation")
        self.assertEqual(nreservs[0].product_id.id,
                         self.hotel_room_simple_101.product_id.id,
                         "Invalid room assigned")
        self.assertEqual(nreservs[1].product_id.id,
                         self.hotel_room_simple_100.product_id.id,
                         "Invalid room assigned")

    def test_invalid_booking(self):
        now_utc_dt = date_utils.now()
        checkin_utc_dt = now_utc_dt + timedelta(days=3)
        checkin_dt = date_utils.dt_as_timezone(checkin_utc_dt,
                                               self.tz_hotel)
        checkout_utc_dt = checkin_utc_dt + timedelta(days=2)
        date_diff = date_utils.date_diff(checkin_utc_dt, checkout_utc_dt,
                                         hours=False) + 1

        # Invalid Occupancy
        wbooks = [self.create_wubook_booking(
            self.user_hotel_manager,
            checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            self.partner_2,
            {
                self.hotel_room_type_budget.wrid: {
                    'occupancy': [3],
                    'dayprices': [15.0, 15.0]
                }
            }
        )]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertTrue(errors, "Invalid reservation created")
        self.assertFalse(any(processed_rids), "Invalid reservation created")

        # No Real Rooms Avail
        wbooks = [self.create_wubook_booking(
            self.user_hotel_manager,
            checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            self.partner_2,
            {
                self.hotel_room_type_special.wrid: {
                    'occupancy': [2, 1],
                    'dayprices': [15.0, 15.0]
                }
            }
        )]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertFalse(errors, "Invalid reservation created")
        self.assertTrue(any(processed_rids), "Invalid reservation created")

        nreservs = self.env['hotel.reservation'].search([
            ('wrid', 'in', processed_rids)
        ], order='id ASC')

        self.assertEqual(nreservs[0].state,
                         'draft',
                         "Overbooking don't handled")
        self.assertTrue(nreservs[1].overbooking,
                        "Overbooking don't handled")

        # No Real Rooms Avail
        wbooks = [
            self.create_wubook_booking(
                self.user_hotel_manager,
                checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                self.partner_2,
                {
                    self.hotel_room_type_special.wrid: {
                        'occupancy': [2],   # 2 Reservation Line
                        'dayprices': [15.0, 15.0]   # 2 Days
                    }
                }
            ),
            self.create_wubook_booking(
                self.user_hotel_manager,
                (checkin_dt - timedelta(days=1)).strftime(
                                            DEFAULT_SERVER_DATETIME_FORMAT),
                self.partner_2,
                {
                    self.hotel_room_type_special.wrid: {
                        'occupancy': [2],   # 2 Reservation Line
                        'dayprices': [15.0, 15.0]   # 2 Days
                    }
                }
            ),
            self.create_wubook_booking(
                self.user_hotel_manager,
                (checkin_dt + timedelta(days=1)).strftime(
                                            DEFAULT_SERVER_DATETIME_FORMAT),
                self.partner_2,
                {
                    self.hotel_room_type_special.wrid: {
                        'occupancy': [2],   # 2 Reservation Line
                        'dayprices': [15.0, 15.0]   # 2 Days
                    }
                }
            ),
        ]

        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertEqual(len(processed_rids), 3, "Invalid Reservation created")
        self.assertFalse(errors, "Invalid Reservation created")
        nreservs = self.env['hotel.reservation'].search([
            ('wrid', 'in', processed_rids)
        ], order='id ASC')
        for nreserv in nreservs:
            self.assertTrue(nreserv.overbooking, "Overbooking don't handled")

    def text_invalid_booking_amount(self):
        now_utc_dt = date_utils.now()
        checkin_utc_dt = now_utc_dt + timedelta(days=3)
        checkin_dt = date_utils.dt_as_timezone(checkin_utc_dt,
                                               self.tz_hotel)

        # Create Reservation
        num_issues = self.env['wubook.issue'].search_count([])
        nbook = self.create_wubook_booking(
            self.user_hotel_manager,
            checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            self.partner_2,
            {
                self.hotel_room_type_special.wrid: {
                    'occupancy': [2],   # 2 Reservation Line
                    'dayprices': [15.0, 15.0]   # 2 Days
                }
            }, channel=self.wubook_channel_test.wid)
        nbook['amount'] = 30.75
        wbooks = [nbook]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertEqual(len(processed_rids), 1, "Reservation not found")
        self.assertFalse(errors, "Reservation errors")
        self.assertNotEqual(self.env['wubook.issue'].search_count([]), num_issues)

    def test_overbooking(self):
        now_utc_dt = date_utils.now()
        checkin_utc_dt = now_utc_dt + timedelta(days=3)
        checkin_dt = date_utils.dt_as_timezone(checkin_utc_dt, self.tz_hotel)

        # Invalid Occupancy
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
                self.partner_2,
                {
                    self.hotel_room_type_budget.wrid: {
                        'occupancy': [1],
                        'dayprices': [15.0, 15.0]
                    }
                }
            )]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertFalse(errors, "Overbooking don't handled")
        self.assertTrue(any(processed_rids), "Overbooking don't handled")
        nreservs = self.env['hotel.reservation'].search([
            ('wrid', 'in', processed_rids)
        ], order="id ASC")
        self.assertFalse(nreservs[0].overbooking,
                         "Overbooking don't handled")
        self.assertFalse(nreservs[1].overbooking,
                         "Overbooking don't handled")
        self.assertTrue(nreservs[2].overbooking,
                        "Overbooking don't handled")

    def test_generate_room_values(self):
        now_utc_dt = date_utils.now()
        checkin_utc_dt = now_utc_dt + timedelta(days=3)
        checkin_dt = date_utils.dt_as_timezone(checkin_utc_dt,
                                               self.tz_hotel)
        checkout_utc_dt = checkin_utc_dt + timedelta(days=1)
        checkout_dt = date_utils.dt_as_timezone(checkout_utc_dt,
                                                self.tz_hotel)
        room_type_restr_item_obj = self.env['hotel.room.type.restriction.item']

        room_types = [self.hotel_room_type_budget, self.hotel_room_type_special]
        values = self.create_wubook_rooms_values(
            room_types,
            [{
                'closed_arrival': 0,
                'booked': 0,
                'max_stay_arrival': 9,
                'max_stay': 0,
                'price': 150.0,
                'min_stay': 0,
                'closed_departure': '1',
                'avail': 0,
                'closed': 0,
                'min_stay_arrival': 0,
                'no_ota': 0,
            }, {
                'closed_arrival': 0,
                'booked': 0,
                'max_stay_arrival': 9,
                'max_stay': 0,
                'price': 50.0,
                'min_stay': 0,
                'closed_departure': '1',
                'avail': 0,
                'closed': 0,
                'min_stay_arrival': 0,
                'no_ota': 0,
            }])
        self.env['wubook'].sudo().generate_room_values(
            checkin_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            checkout_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            values)

        for room_type in room_types:
            items = room_type_restr_item_obj.search([
                ('room_type_id', '=', room_type.id),
                ('date_start',
                 '>=', checkin_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                ('date_end',
                 '<=', checkout_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                ('restriction_id', '=', self.restriction_default_id)
            ])
            self.assertTrue(any(items),
                            "Hotel Wubook Invalid fetch room values")
            for item in items:
                self.assertTrue(
                    item.closed_departure,
                    "Hotel Wubook Invalid fetch room values")
                self.assertEqual(
                    item.max_stay_arrival,
                    9,
                    "Hotel Wubook Invalid fetch room values")
