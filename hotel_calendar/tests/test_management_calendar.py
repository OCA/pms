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
from openerp.exceptions import ValidationError
from .common import TestHotelCalendar
from odoo.addons.hotel import date_utils
import logging
_logger = logging.getLogger(__name__)


class TestManagementCalendar(TestHotelCalendar):

    def test_calendar_prices(self):
        now_utc_dt = date_utils.now()
        adv_utc_dt = now_utc_dt + timedelta(days=15)

        vrooms = (self.hotel_vroom_budget, self.hotel_vroom_special)

        hotel_cal_mngt_obj = self.env['hotel.calendar.management'].sudo(
                                                    self.user_hotel_manager)

        hcal_data = hotel_cal_mngt_obj.get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            self.parity_pricelist_id,
            self.parity_restrictions_id,
            True)
        for vroom in vrooms:
            for k_pr, v_pr in hcal_data['prices'].iteritems():
                if k_pr == vroom.id:    # Only Check Test Cases
                    for k_info, v_info in enumerate(v_pr):
                        if k_info >= len(self.prices_tmp[vroom.id]):
                            break
                        self.assertEqual(v_info['price'],
                                         self.prices_tmp[vroom.id][k_info],
                                         "Hotel Calendar Management Prices \
                                            doesn't match!")

        # REMOVE PRICES
        prices_obj = self.env['product.pricelist.item'].sudo(
                                                    self.user_hotel_manager)
        prod_tmpl_ids = (
            self.hotel_vroom_budget.product_id.product_tmpl_id.id,
            self.hotel_vroom_special.product_id.product_tmpl_id.id
        )
        pr_ids = prices_obj.search([
            ('pricelist_id', '=', self.parity_pricelist_id),
            ('product_tmpl_id', 'in', prod_tmpl_ids),
        ])
        pr_ids.sudo(self.user_hotel_manager).unlink()

        hcal_data = hotel_cal_mngt_obj.get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            self.parity_pricelist_id,
            self.parity_restrictions_id,
            True)
        self.assertFalse(any(hcal_data['prices']), "Hotel Calendar Management \
                                        Prices doesn't match after remove!")

    def test_calendar_restrictions(self):
        now_utc_dt = date_utils.now()
        adv_utc_dt = now_utc_dt + timedelta(days=15)
        vrooms = (self.hotel_vroom_budget, self.hotel_vroom_special)

        hotel_cal_mngt_obj = self.env['hotel.calendar.management'].sudo(
                                                    self.user_hotel_manager)

        hcal_data = hotel_cal_mngt_obj.get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            self.parity_pricelist_id,
            self.parity_restrictions_id,
            True)
        for vroom in vrooms:
            for k_pr, v_pr in hcal_data['restrictions'].iteritems():
                if k_pr == vroom.id:    # Only Check Test Cases
                    for k_info, v_info in enumerate(v_pr):
                        rest_items = self.restrictions_min_stay_tmp[vroom.id]
                        if k_info >= len(rest_items):
                            break
                        self.assertEqual(
                            v_info['min_stay'],
                            self.restrictions_min_stay_tmp[vroom.id][k_info],
                            "Hotel Calendar Management Restrictions \
                                doesn't match!")

        # REMOVE RESTRICTIONS
        rest_it_obj = self.env['hotel.room.type.restriction.item'].sudo(
                                                    self.user_hotel_manager)
        rest_ids = rest_it_obj.search([
            ('applied_on', '=', '0_room_type'),
            ('restriction_id', '=', self.parity_restrictions_id),
            ('room_type_id', 'in', (self.hotel_vroom_budget.id,
                                       self.hotel_vroom_special.id)),
        ])
        rest_ids.sudo(self.user_hotel_manager).unlink()

        hcal_data = hotel_cal_mngt_obj.get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            self.parity_pricelist_id,
            self.parity_restrictions_id,
            True)
        self.assertFalse(
            any(hcal_data['restrictions']),
            "Hotel Calendar Management Restrictions doesn't match \
                                                                after remove!")

    def test_calendar_availability(self):
        now_utc_dt = date_utils.now()
        adv_utc_dt = now_utc_dt + timedelta(days=6)
        vrooms = (self.hotel_vroom_budget, self.hotel_vroom_special)

        hotel_cal_mngt_obj = self.env['hotel.calendar.management'].sudo(
                                                    self.user_hotel_manager)
        vroom_avail_obj = self.env['hotel.room.type.availability'].sudo(
                                                    self.user_hotel_manager)

        hcal_data = hotel_cal_mngt_obj.get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            self.parity_pricelist_id,
            self.parity_restrictions_id,
            True)
        for vroom in vrooms:
            for k_pr, v_pr in hcal_data['availability'].iteritems():
                if k_pr == vroom.id:    # Only Check Test Cases
                    for k_info, v_info in enumerate(v_pr):
                        if k_info >= len(self.avails_tmp[vroom.id]):
                            break
                        self.assertEqual(
                            v_info['avail'],
                            self.avails_tmp[vroom.id][k_info],
                            "Hotel Calendar Management Availability \
                                                            doesn't match!")

        # CHANGE AVAIL
        avail_ids = vroom_avail_obj.search([
            ('room_type_id', 'in', (self.hotel_vroom_budget.id,
                                       self.hotel_vroom_special.id)),
        ])
        for avail_id in avail_ids:
            avail_id.sudo(self.user_hotel_manager).write({'avail': 1})
        hcal_data = hotel_cal_mngt_obj.get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            self.parity_pricelist_id,
            self.parity_restrictions_id,
            True)
        for vroom in vrooms:
            for k_pr, v_pr in hcal_data['availability'].iteritems():
                if k_pr == vroom.id:    # Only Check Test Cases
                    for k_info, v_info in enumerate(v_pr):
                        self.assertEqual(
                            v_info['avail'],
                            1,
                            "Hotel Calendar Management Availability \
                                                            doesn't match!")

        # REMOVE AVAIL
        avail_ids = vroom_avail_obj.search([
            ('room_type_id', 'in', (self.hotel_vroom_budget.id,
                                       self.hotel_vroom_special.id)),
        ])
        avail_ids.sudo(self.user_hotel_manager).unlink()

        hcal_data = hotel_cal_mngt_obj.get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            self.parity_pricelist_id,
            self.parity_restrictions_id,
            True)
        for vroom in vrooms:
            for k_pr, v_pr in hcal_data['availability'].iteritems():
                if k_pr == vroom.id:    # Only Check Test Cases
                    for k_info, v_info in enumerate(v_pr):
                        self.assertEqual(
                            v_info['avail'],
                            vroom.max_real_rooms,
                            "Hotel Calendar Management Availability \
                                                            doesn't match!")

    def test_save_changes(self):
        now_utc_dt = date_utils.now()
        adv_utc_dt = now_utc_dt + timedelta(days=3)
        vrooms = (self.hotel_vroom_budget,)

        hotel_cal_mngt_obj = self.env['hotel.calendar.management'].sudo(
                                                    self.user_hotel_manager)

        # Generate new prices
        prices = (144.0, 170.0, 30.0, 50.0)
        cprices = {}
        for k_item, v_item in enumerate(prices):
            ndate_utc_dt = now_utc_dt + timedelta(days=k_item)
            cprices.setdefault(self.hotel_vroom_budget.id, []).append({
                'date': ndate_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'price': v_item
            })

        # Generate new restrictions
        restrictions = {
            'min_stay': (3, 2, 4, 1),
            'max_stay': (5, 8, 9, 3),
            'min_stay_arrival': (2, 3, 6, 2),
            'max_stay_arrival': (4, 7, 7, 4),
            'closed_departure': (False, True, False, True),
            'closed_arrival': (True, False, False, False),
            'closed': (False, False, True, True),
        }
        crestrictions = {}
        for i in range(0, 4):
            ndate_utc_dt = now_utc_dt + timedelta(days=i)
            crestrictions.setdefault(self.hotel_vroom_budget.id, []).append({
                'date': ndate_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'closed_arrival': restrictions['closed_arrival'][i],
                'max_stay': restrictions['max_stay'][i],
                'min_stay': restrictions['min_stay'][i],
                'closed_departure': restrictions['closed_departure'][i],
                'closed': restrictions['closed'][i],
                'min_stay_arrival': restrictions['min_stay_arrival'][i],
                'max_stay_arrival': restrictions['max_stay_arrival'][i],
            })

        # Generate new availability
        avails = (1, 2, 2, 1)
        cavails = {}
        for k_item, v_item in enumerate(avails):
            ndate_utc_dt = now_utc_dt + timedelta(days=k_item)
            ndate_dt = date_utils.dt_as_timezone(ndate_utc_dt, self.tz_hotel)
            cavails.setdefault(self.hotel_vroom_budget.id, []).append({
                'date': ndate_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'avail': v_item,
                'no_ota': False,
            })

        # Save new values
        hotel_cal_mngt_obj.save_changes(
            self.parity_pricelist_id,
            self.parity_restrictions_id,
            cprices,
            crestrictions,
            cavails)

        # Check data integrity
        hcal_data = hotel_cal_mngt_obj.get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            self.parity_pricelist_id,
            self.parity_restrictions_id,
            True)

        for vroom in vrooms:
            for k_pr, v_pr in hcal_data['availability'].iteritems():
                if k_pr == vroom.id:    # Only Check Test Cases
                    for k_info, v_info in enumerate(v_pr):
                        self.assertEqual(v_info['avail'],
                                         avails[k_info],
                                         "Hotel Calendar Management \
                                                Availability doesn't match!")
            for k_pr, v_pr in hcal_data['restrictions'].iteritems():
                if k_pr == vroom.id:    # Only Check Test Cases
                    for k_info, v_info in enumerate(v_pr):
                        self.assertEqual(v_info['min_stay'],
                                         restrictions['min_stay'][k_info],
                                         "Hotel Calendar Management \
                                                Restrictions doesn't match!")
                        self.assertEqual(v_info['max_stay'],
                                         restrictions['max_stay'][k_info],
                                         "Hotel Calendar Management \
                                                Restrictions doesn't match!")
                        self.assertEqual(
                            v_info['min_stay_arrival'],
                            restrictions['min_stay_arrival'][k_info],
                            "Hotel Calendar Management Restrictions \
                                                            doesn't match!")
                        self.assertEqual(
                            v_info['max_stay_arrival'],
                            restrictions['max_stay_arrival'][k_info],
                            "Hotel Calendar Management Restrictions \
                                                            doesn't match!")
                        self.assertEqual(
                            v_info['closed_departure'],
                            restrictions['closed_departure'][k_info],
                            "Hotel Calendar Management Restrictions \
                                                            doesn't match!")
                        self.assertEqual(
                            v_info['closed_arrival'],
                            restrictions['closed_arrival'][k_info],
                            "Hotel Calendar Management Restrictions \
                                                            doesn't match!")
                        self.assertEqual(
                            v_info['closed'],
                            restrictions['closed'][k_info],
                            "Hotel Calendar Management Restrictions \
                                                            doesn't match!")
            for k_pr, v_pr in hcal_data['prices'].iteritems():
                if k_pr == vroom.id:    # Only Check Test Cases
                    for k_info, v_info in enumerate(v_pr):
                        self.assertEqual(v_info['price'],
                                         prices[k_info], "Hotel Calendar \
                                            Management Prices doesn't match!")

    def test_calendar_reservations(self):
        now_utc_dt = date_utils.now()
        adv_utc_dt = now_utc_dt + timedelta(days=15)
        vrooms = (self.hotel_vroom_budget,)

        hotel_cal_mngt_obj = self.env['hotel.calendar.management'].sudo(
                                                    self.user_hotel_manager)

        reserv_start_utc_dt = now_utc_dt + timedelta(days=3)
        reserv_end_utc_dt = reserv_start_utc_dt + timedelta(days=3)
        folio = self.create_folio(self.user_hotel_manager, self.partner_2)
        reservation = self.create_reservation(
            self.user_hotel_manager,
            folio,
            reserv_start_utc_dt,
            reserv_end_utc_dt,
            self.hotel_room_simple_100,
            "Reservation Test #1")

        hcal_data = hotel_cal_mngt_obj.get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            self.parity_pricelist_id,
            self.parity_restrictions_id,
            True)

        avail_end_utc_dt = reserv_end_utc_dt - timedelta(days=1)
        for vroom in vrooms:
            for k_pr, v_pr in hcal_data['count_reservations'].iteritems():
                if k_pr == vroom.id:    # Only Check Test Cases
                    for k_info, v_info in enumerate(v_pr):
                        ndate = date_utils.get_datetime(v_info['date'])
                        if date_utils.date_in(ndate,
                                              reserv_start_utc_dt,
                                              avail_end_utc_dt) == 0:
                            self.assertEqual(v_info['num'],
                                             1,
                                             "Hotel Calendar Management \
                                                Availability doesn't match!")

    def test_invalid_input_calendar_data(self):
        now_utc_dt = date_utils.now()
        adv_utc_dt = now_utc_dt + timedelta(days=15)

        hotel_cal_mngt_obj = self.env['hotel.calendar.management'].sudo(
                                                    self.user_hotel_manager)

        with self.assertRaises(ValidationError):
            hcal_data = hotel_cal_mngt_obj.get_hcalendar_all_data(
                False,
                adv_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                self.parity_pricelist_id,
                self.parity_restrictions_id,
                True)
        with self.assertRaises(ValidationError):
            hcal_data = hotel_cal_mngt_obj.get_hcalendar_all_data(
                now_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                False,
                self.parity_pricelist_id,
                self.parity_restrictions_id,
                True)
        with self.assertRaises(ValidationError):
            hcal_data = hotel_cal_mngt_obj.get_hcalendar_all_data(
                False,
                False,
                self.parity_pricelist_id,
                self.parity_restrictions_id,
                True)
        hcal_data = hotel_cal_mngt_obj.get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            False,
            False,
            True)
        self.assertTrue(any(hcal_data), "Hotel Calendar invalid default \
                                                    management parity models!")

    def test_calendar_settings(self):
        hotel_cal_mngt_obj = self.env['hotel.calendar.management'].sudo(
                                                    self.user_hotel_manager)
        settings = hotel_cal_mngt_obj.get_hcalendar_settings()
        self.assertTrue(settings, "Hotel Calendar invalid settings")

        self.assertEqual(settings['eday_week'],
                         self.user_hotel_manager.npms_end_day_week,
                         "Hotel Calendar invalid settings")
        self.assertEqual(settings['eday_week_offset'],
                         self.user_hotel_manager.npms_end_day_week_offset,
                         "Hotel Calendar invalid settings")
        self.assertEqual(settings['days'],
                         self.user_hotel_manager.npms_default_num_days,
                         "Hotel Calendar invalid settings")
        self.assertEqual(settings['show_notifications'],
                         self.user_hotel_manager.pms_show_notifications,
                         "Hotel Calendar invalid settings")
        self.assertEqual(settings['show_num_rooms'],
                         self.user_hotel_manager.pms_show_num_rooms,
                         "Hotel Calendar invalid settings")
