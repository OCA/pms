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
from odoo import api
from odoo.addons.hotel import date_utils
from odoo.addons.hotel.tests.common import TestHotel
from odoo.addons.hotel_wubook_proto.wubook import (
    DEFAULT_WUBOOK_DATE_FORMAT,
    DEFAULT_WUBOOK_TIME_FORMAT,
    WUBOOK_STATUS_CONFIRMED,
    WUBOOK_STATUS_CANCELLED)
from random import randint
import logging
_logger = logging.getLogger(__name__)


class TestHotelWubook(TestHotel):

    @classmethod
    def _init_mock_hotel(cls):
        super(TestHotelWubook, cls)._init_mock_hotel()

        
        def wubook_ommit(self, *args, **kwargs):
            return True

        @api.model
        def wubook_create_channel_connector_issue(self, section, message, wmessage,
                                       wid=False, dfrom=False, dto=False):
            _logger.info("ISSUE CREATED:\n\t- %s\n\t--- %s", section, message)

        cls.env['wubook']._patch_method('create_channel_connector_issue',
                                        wubook_create_channel_connector_issue)
        cls.env['wubook']._patch_method('is_valid_account', wubook_ommit)
        cls.env['wubook']._patch_method('initialize', wubook_ommit)
        cls.env['wubook']._patch_method('push_activation', wubook_ommit)
        cls.env['wubook']._patch_method('init_connection', wubook_ommit)
        cls.env['wubook']._patch_method('close_connection', wubook_ommit)
        cls.env['wubook']._patch_method('create_room', wubook_ommit)
        cls.env['wubook']._patch_method('modify_room', wubook_ommit)
        cls.env['wubook']._patch_method('delete_room', wubook_ommit)
        cls.env['wubook']._patch_method('import_rooms', wubook_ommit)
        cls.env['wubook']._patch_method('fetch_rooms_values', wubook_ommit)
        cls.env['wubook']._patch_method('update_availability', wubook_ommit)
        cls.env['wubook']._patch_method('corporate_fetch', wubook_ommit)
        cls.env['wubook']._patch_method('create_reservation', wubook_ommit)
        cls.env['wubook']._patch_method('cancel_reservation', wubook_ommit)
        cls.env['wubook']._patch_method('fetch_new_bookings', wubook_ommit)
        cls.env['wubook']._patch_method('fetch_booking', wubook_ommit)
        cls.env['wubook']._patch_method('mark_bookings', wubook_ommit)
        cls.env['wubook']._patch_method('create_plan', wubook_ommit)
        cls.env['wubook']._patch_method('delete_plan', wubook_ommit)
        cls.env['wubook']._patch_method('update_plan_name', wubook_ommit)
        cls.env['wubook']._patch_method('update_plan_prices', wubook_ommit)
        cls.env['wubook']._patch_method('update_plan_periods', wubook_ommit)
        cls.env['wubook']._patch_method('import_pricing_plans', wubook_ommit)
        cls.env['wubook']._patch_method('fetch_plan_prices', wubook_ommit)
        cls.env['wubook']._patch_method('fetch_all_plan_prices', wubook_ommit)
        cls.env['wubook']._patch_method('import_restriction_plans',
                                        wubook_ommit)
        cls.env['wubook']._patch_method('fetch_rplan_restrictions',
                                        wubook_ommit)
        cls.env['wubook']._patch_method('update_rplan_values', wubook_ommit)
        cls.env['wubook']._patch_method('create_rplan', wubook_ommit)
        cls.env['wubook']._patch_method('rename_rplan', wubook_ommit)
        cls.env['wubook']._patch_method('delete_rplan', wubook_ommit)
        cls.env['wubook']._patch_method('import_channels_info', wubook_ommit)
        cls.env['wubook']._patch_method('push_changes', wubook_ommit)
        cls.env['wubook']._patch_method('push_availability', wubook_ommit)
        cls.env['wubook']._patch_method('push_priceplans', wubook_ommit)
        cls.env['wubook']._patch_method('push_restrictions', wubook_ommit)

    def create_wubook_booking(self, creator, checkin, partner, rinfo,
                              channel=0, notes=''):
        rcode = randint(100000, 999999)
        crcode = randint(100000, 999999)
        brate = randint(100000, 999999)
        id_woodoo = randint(100000, 999999)

        if not partner.email or partner.email == '':
            self.raiseException("Partner doesn't have a mail")

        now_utc_dt = date_utils.now()
        now_dt = date_utils.dt_as_timezone(now_utc_dt, self.tz_hotel)
        checkin_utc_dt = date_utils.get_datetime(checkin)
        checkin_dt = date_utils.dt_as_timezone(checkin_utc_dt, self.tz_hotel)
        numdays = 0
        for k_room, v_room in rinfo.iteritems():
            numdays = max(len(v_room['dayprices']), numdays)
        checkout_utc_dt = checkin_utc_dt + timedelta(days=numdays)
        checkout_dt = date_utils.dt_as_timezone(checkout_utc_dt, self.tz_hotel)
        date_diff = date_utils.date_diff(checkin_utc_dt, checkout_utc_dt,
                                         hours=False)

        # Generate Day Prices
        dayprices = {}
        total_amount = 0.0
        for k_room, v_room in rinfo.iteritems():
            for price in v_room['dayprices']:
                dayprices.setdefault(k_room, []).append(price)
                total_amount += price
        # Generate Values
        rooms = []
        rooms_occu = []
        booked_rooms = []
        room_type_obj = self.env['hotel.room.type']
        max_persons = 0
        for k_room, v_room in rinfo.iteritems():
            room_type = room_type_obj.search([
                ('wrid', '=', k_room)
            ], limit=1)
            # Generate Rooms
            for price in range(0, len(v_room['occupancy'])):
                rooms.append(k_room)
            # Generate Rooms Occupancies
            for val in v_room['occupancy']:
                # Generate Rooms Occupancies
                rooms_occu.append({
                    'id': k_room,
                    'occupancy': val,
                })
                # Generate Booked Rooms
                roomdays = []
                for k_price, v_price in enumerate(v_room['dayprices']):
                    ndate = checkin_dt + timedelta(days=k_price)
                    roomdays.append({
                        'ancillary': {},
                        'rate_id': 3,
                        'price': v_price,
                        'day': ndate.strftime(DEFAULT_WUBOOK_DATE_FORMAT)
                    })
                booked_rooms.append({
                    'ancillary': {
                        'channel_room_id': 1,
                        'channel_room_name': room_type.name,
                        'addons': [],
                        'guests': val
                    },
                    'room_id': k_room,
                    'roomdays': roomdays
                })
                if val > max_persons:
                    max_persons = val

        return {
            'id_channel': channel,
            'special_offer': '',
            'reservation_code': rcode,
            'dayprices': dayprices,
            'arrival_hour': checkin_dt.strftime(DEFAULT_WUBOOK_TIME_FORMAT),
            'booked_rate': brate,
            'rooms': ','.join(map(str, rooms)),
            'customer_mail': partner.email,
            'customer_country': 'ES',
            'children': 0,
            'payment_gateway_fee': '',
            'modified_reservations': [],
            'customer_surname': ' '.join(partner.name.split(' ')[1:]),
            'date_departure': checkout_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            'amount_reason': '',
            'customer_city': partner.city,
            'opportunities': 0,
            'date_received': now_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            'rooms_occupancies': rooms_occu,
            'sessionSeed': '',
            'booked_rooms': booked_rooms,
            'customer_name': partner.name.split(' ')[0],
            'date_arrival': checkin_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            'status': WUBOOK_STATUS_CONFIRMED,
            'was_modified': 0,
            'channel_reservation_code': crcode,
            'men': max_persons,
            'orig_amount': total_amount,
            'customer_phone': partner.mobile or partner.phone or '',
            'customer_notes': notes,
            'customer_address': partner.street,
            'device': -1,
            'addons_list': [],
            'status_reason': '',
            'roomnight': date_diff-1,
            'boards': '',
            'customer_language': 32,
            'fount': '',
            'channel_data': {},
            'room_opportunities': 0,
            'customer_zip': partner.zip,
            'amount': total_amount,
            'id_woodoo': id_woodoo,
            'cc_info': 1,
            'customer_language_iso': 'es'
        }

    def create_wubook_rooms_values(self, rooms, values):
        json_data = {}
        _logger.info("=== PASA AAA")
        _logger.info(values)
        for room in rooms:
            for cvalue in values:
                json_data.setdefault(room.wrid, []).append({
                    'closed_arrival': cvalue['closed_arrival'],
                    'booked': cvalue['booked'],
                    'max_stay_arrival': cvalue['max_stay_arrival'],
                    'max_stay': cvalue['max_stay'],
                    'price': cvalue['price'],
                    'min_stay': cvalue['min_stay'],
                    'closed_departure': cvalue['closed_departure'],
                    'avail': cvalue['avail'],
                    'closed': cvalue['closed'],
                    'min_stay_arrival': cvalue['min_stay_arrival'],
                    'no_ota': cvalue['no_ota'],
                })
        return json_data

    def cancel_booking(self, wbooking):
        wbooking['status'] = WUBOOK_STATUS_CANCELLED
        return wbooking

    @classmethod
    def setUpClass(cls):
        super(TestHotelWubook, cls).setUpClass()

        # Update Test Virtual Rooms
        cls.hotel_room_type_budget.write({
            'wcapacity': 1,
            'wrid': 3000,
            'wscode': 'T001',
        })
        cls.hotel_room_type_special.write({
            'wcapacity': 2,
            'wrid': 3001,
            'wscode': 'T002',
        })

        # Update Restriction
        room_type_restr_obj = cls.env['hotel.room.type.restriction']
        default_restriction = room_type_restr_obj.search([
            ('wpid', '=', '0')
        ], limit=1)
        if default_restriction:
            cls.restriction_default_id = default_restriction.id
        else:
            cls.restriction_1.write({
                'wpid': '0'
            })
            cls.restriction_default_id = cls.restriction_1.id

        # Create Some Wubook Info
        cls.wubook_channel_test = cls.env['wubook.channel.info'].create({
            'wid': 1,
            'name': 'Channel Test'
        })

    @classmethod
    def tearDownClass(cls):
        # Remove mocks
        cls.env['wubook']._revert_method('create_channel_connector_issue')
        cls.env['wubook']._revert_method('is_valid_account')
        cls.env['wubook']._revert_method('initialize')
        cls.env['wubook']._revert_method('push_activation')
        cls.env['wubook']._revert_method('init_connection')
        cls.env['wubook']._revert_method('close_connection')
        cls.env['wubook']._revert_method('create_room')
        cls.env['wubook']._revert_method('modify_room')
        cls.env['wubook']._revert_method('delete_room')
        cls.env['wubook']._revert_method('import_rooms')
        cls.env['wubook']._revert_method('fetch_rooms_values')
        cls.env['wubook']._revert_method('update_availability')
        cls.env['wubook']._revert_method('corporate_fetch')
        cls.env['wubook']._revert_method('create_reservation')
        cls.env['wubook']._revert_method('cancel_reservation')
        cls.env['wubook']._revert_method('fetch_new_bookings')
        cls.env['wubook']._revert_method('fetch_booking')
        cls.env['wubook']._revert_method('mark_bookings')
        cls.env['wubook']._revert_method('create_plan')
        cls.env['wubook']._revert_method('delete_plan')
        cls.env['wubook']._revert_method('update_plan_name')
        cls.env['wubook']._revert_method('update_plan_prices')
        cls.env['wubook']._revert_method('update_plan_periods')
        cls.env['wubook']._revert_method('import_pricing_plans')
        cls.env['wubook']._revert_method('fetch_plan_prices')
        cls.env['wubook']._revert_method('fetch_all_plan_prices')
        cls.env['wubook']._revert_method('import_restriction_plans')
        cls.env['wubook']._revert_method('fetch_rplan_restrictions')
        cls.env['wubook']._revert_method('update_rplan_values')
        cls.env['wubook']._revert_method('create_rplan')
        cls.env['wubook']._revert_method('rename_rplan')
        cls.env['wubook']._revert_method('delete_rplan')
        cls.env['wubook']._revert_method('import_channels_info')

        super(TestHotelWubook, cls).tearDownClass()
