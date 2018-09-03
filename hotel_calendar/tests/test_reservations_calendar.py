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
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import ValidationError
from .common import TestHotelCalendar
from odoo.addons.hotel import date_utils
import pytz


class TestReservationsCalendar(TestHotelCalendar):

    def test_calendar_pricelist(self):
        now_utc_dt = date_utils.now()
        real_start_utc_dt = (now_utc_dt - timedelta(days=1))
        adv_utc_dt = now_utc_dt + timedelta(days=15)

        hotel_reserv_obj = self.env['hotel.reservation'].sudo(
                                                    self.user_hotel_manager)

        hcal_data = hotel_reserv_obj.get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT))

        # Check Pricelist Integrity
        for k_pr, v_pr in hcal_data['pricelist'].iteritems():
            for vroom_pr in v_pr:
                # Only Check Test Cases
                if vroom_pr['room'] in self.prices_tmp.keys():
                    sorted_dates = sorted(
                        vroom_pr['days'].keys(),
                        key=lambda x: datetime.datetime.strptime(x, '%d/%m/%Y')
                    )
                    init_date_dt = datetime.datetime.strptime(
                        sorted_dates[0],
                        '%d/%m/%Y').replace(tzinfo=pytz.utc)
                    end_date_dt = datetime.datetime.strptime(
                        sorted_dates[-1],
                        '%d/%m/%Y').replace(tzinfo=pytz.utc)

                    self.assertEqual(real_start_utc_dt, init_date_dt,
                                     "Hotel Calendar don't start in \
                                                            the correct date!")
                    self.assertEqual(adv_utc_dt, end_date_dt,
                                     "Hotel Calendar don't end in \
                                                            the correct date!")

                    vroom_prices = self.prices_tmp[vroom_pr['room']]
                    for k_price, v_price in enumerate(vroom_prices):
                        self.assertEqual(
                            v_price,
                            vroom_pr['days'][sorted_dates[k_price+1]],
                            "Hotel Calendar Pricelist doesn't match!")

        # Check Pricelist Integrity after unlink
        pricelist_item_obj = self.env['product.pricelist.item'].sudo(
                                                    self.user_hotel_manager)
        pr_ids = pricelist_item_obj.search([
            ('pricelist_id', '=', self.parity_pricelist_id),
            ('product_tmpl_id', 'in', (
                self.hotel_vroom_budget.product_id.product_tmpl_id.id,
                self.hotel_vroom_special.product_id.product_tmpl_id.id)),
        ])
        pr_ids.sudo(self.user_hotel_manager).unlink()
        reserv_obj = self.env['hotel.reservation'].sudo(
                                                    self.user_hotel_manager)
        hcal_data = reserv_obj.get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
        vrooms = (self.hotel_vroom_budget, self.hotel_vroom_special)
        for vroom in vrooms:
            for k_pr, v_pr in hcal_data['pricelist'].iteritems():
                for vroom_pr in v_pr:
                    if vroom_pr['room'] == vroom.id:    # Only Check Test Cases
                        self.assertEqual(
                            vroom.list_price,
                            vroom_pr['days'][sorted_dates[k_price+1]],
                            "Hotel Calendar Pricelist doesn't \
                                                        match after remove!")

    def test_calendar_reservations(self):
        now_utc_dt = date_utils.now()
        adv_utc_dt = now_utc_dt + timedelta(days=15)

        hotel_reserv_obj = self.env['hotel.reservation'].sudo(
                                                    self.user_hotel_manager)

        def is_reservation_listed(reservation_id):
            hcal_data = hotel_reserv_obj.get_hcalendar_all_data(
                now_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                adv_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
            # TODO: Perhaps not the best way to do this test... :/
            hasReservationTest = False
            for reserv in hcal_data['reservations']:
                if reserv[1] == reservation_id:
                    hasReservationTest = True
                    break
            return hasReservationTest

        # CREATE COMPLETE RESERVATION (3 Nigths)
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

        # CHECK SUCCESSFULL CREATION
        self.assertTrue(is_reservation_listed(reservation.id),
                        "Hotel Calendar can't found test reservation!")

        # CONFIRM FOLIO
        folio.sudo(self.user_hotel_manager).action_confirm()
        self.assertTrue(is_reservation_listed(reservation.id),
                        "Hotel Calendar can't found test reservation!")

        # CALENDAR LIMITS
        now_utc_dt_tmp = now_utc_dt
        adv_utc_dt_tmp = adv_utc_dt
        # Start after reservation end
        now_utc_dt = reserv_end_utc_dt + timedelta(days=2)
        adv_utc_dt = now_utc_dt + timedelta(days=15)
        self.assertFalse(
            is_reservation_listed(reservation.id),
            "Hotel Calendar found test reservation but expected not found it!")

        # Ends before reservation start
        adv_utc_dt = reserv_start_utc_dt - timedelta(days=1)
        now_utc_dt = adv_utc_dt - timedelta(days=15)
        self.assertFalse(
            is_reservation_listed(reservation.id),
            "Hotel Calendar found test reservation but expected not found it!")
        now_utc_dt = now_utc_dt_tmp
        adv_utc_dt = adv_utc_dt_tmp

        # Start in the middle of the reservation days
        now_utc_dt = reserv_end_utc_dt - timedelta(days=1)
        adv_utc_dt = now_utc_dt + timedelta(days=15)
        self.assertTrue(
            is_reservation_listed(reservation.id),
            "Hotel Calendar can't found test reservation!")
        now_utc_dt = now_utc_dt_tmp
        adv_utc_dt = adv_utc_dt_tmp

        # CANCEL FOLIO
        folio.sudo(self.user_hotel_manager).action_cancel()
        self.assertFalse(
            is_reservation_listed(reservation.id),
            "Hotel Calendar can't found test reservation!")

        # REMOVE FOLIO
        folio.sudo().unlink()   # FIXME: Can't use: self.user_hotel_manager
        self.assertFalse(
            is_reservation_listed(reservation.id),
            "Hotel Calendar can't found test reservation!")

    def test_invalid_input_calendar_data(self):
        now_utc_dt = date_utils.now()
        adv_utc_dt = now_utc_dt + timedelta(days=15)

        hotel_reserv_obj = self.env['hotel.reservation'].sudo(
                                                    self.user_hotel_manager)

        with self.assertRaises(ValidationError):
            hcal_data = hotel_reserv_obj.get_hcalendar_all_data(
                False,
                adv_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
        with self.assertRaises(ValidationError):
            hcal_data = hotel_reserv_obj.get_hcalendar_all_data(
                now_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                False)
        with self.assertRaises(ValidationError):
            hcal_data = hotel_reserv_obj.get_hcalendar_all_data(
                False,
                False)

    def test_calendar_settings(self):
        hcal_options = self.env['hotel.reservation'].sudo(
                            self.user_hotel_manager).get_hcalendar_settings()

        self.assertEqual(hcal_options['divide_rooms_by_capacity'],
                         self.user_hotel_manager.pms_divide_rooms_by_capacity,
                         "Hotel Calendar Invalid Options!")
        self.assertEqual(hcal_options['eday_week'],
                         self.user_hotel_manager.pms_end_day_week,
                         "Hotel Calendar Invalid Options!")
        self.assertEqual(hcal_options['days'],
                         self.user_hotel_manager.pms_default_num_days,
                         "Hotel Calendar Invalid Options!")
        self.assertEqual(
            hcal_options['allow_invalid_actions'],
            self.user_hotel_manager.pms_type_move == 'allow_invalid',
            "Hotel Calendar Invalid Options!")
        self.assertEqual(
            hcal_options['assisted_movement'],
            self.user_hotel_manager.pms_type_move == 'assisted',
            "Hotel Calendar Invalid Options!")
        default_arrival_hour = self.env['ir.default'].sudo().get(
                'res.config.settings', 'default_arrival_hour')
        self.assertEqual(hcal_options['default_arrival_hour'],
                         default_arrival_hour,
                         "Hotel Calendar Invalid Options!")
        default_departure_hour = self.env['ir.default'].sudo().get(
                'res.config.settings', 'default_departure_hour')
        self.assertEqual(hcal_options['default_departure_hour'],
                         default_departure_hour,
                         "Hotel Calendar Invalid Options!")
        self.assertEqual(hcal_options['show_notifications'],
                         self.user_hotel_manager.pms_show_notifications,
                         "Hotel Calendar Invalid Options!")
        self.assertEqual(hcal_options['show_num_rooms'],
                         self.user_hotel_manager.pms_show_num_rooms,
                         "Hotel Calendar Invalid Options!")
        self.assertEqual(hcal_options['show_pricelist'],
                         self.user_hotel_manager.pms_show_pricelist,
                         "Hotel Calendar Invalid Options!")
        self.assertEqual(hcal_options['show_availability'],
                         self.user_hotel_manager.pms_show_availability,
                         "Hotel Calendar Invalid Options!")

    def test_swap_reservation(self):
        hcal_reserv_obj = self.env['hotel.reservation'].sudo(
                            self.user_hotel_manager)
        now_utc_dt = date_utils.now()

        # CREATE RESERVATIONS
        reserv_start_utc_dt = now_utc_dt + timedelta(days=3)
        reserv_end_utc_dt = reserv_start_utc_dt + timedelta(days=3)
        folio_a = self.create_folio(self.user_hotel_manager, self.partner_2)
        reservation_a = self.create_reservation(
            self.user_hotel_manager,
            folio_a,
            reserv_start_utc_dt,
            reserv_end_utc_dt,
            self.hotel_room_double_200,
            "Reservation Test #1")
        self.assertTrue(reservation_a,
                        "Hotel Calendar create test reservation!")
        folio_a.sudo(self.user_hotel_manager).action_confirm()

        folio_b = self.create_folio(self.user_hotel_manager, self.partner_2)
        reservation_b = self.create_reservation(
            self.user_hotel_manager,
            folio_b,
            reserv_start_utc_dt,
            reserv_end_utc_dt,
            self.hotel_room_simple_101,
            "Reservation Test #2")
        self.assertTrue(reservation_b,
                        "Hotel Calendar can't create test reservation!")
        folio_b.sudo(self.user_hotel_manager).action_confirm()

        self.assertTrue(
            hcal_reserv_obj.swap_reservations(reservation_a.ids,
                                              reservation_b.ids),
            "Hotel Calendar invalid swap operation"
        )
        self.assertEqual(reservation_a.product_id.id,
                         self.hotel_room_simple_101.product_id.id,
                         "Hotel Calendar wrong swap operation")
        self.assertEqual(reservation_b.product_id.id,
                         self.hotel_room_double_200.product_id.id,
                         "Hotel Calendar wrong swap operation")
