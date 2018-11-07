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
from odoo import api, fields
from odoo.tests import common
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
from odoo.addons.mail.tests.common import TestMail
from odoo.addons.hotel import date_utils
import pytz
import logging
_logger = logging.getLogger(__name__)


# TestMail crea recursos utiles para nuestros test...
# por ejemplo, usuarios con distintos tipos de nivel, etc...
class TestHotel(TestMail):

    @classmethod
    def _init_mock_hotel(cls):
        return True

    def create_folio(self, creator, partner):
        # Create Folio
        folio = self.env['hotel.folio'].sudo(creator).create({
            'partner_id': partner.id,
        })
        self.assertTrue(folio, "Can't create folio")
        return folio

    def create_reservation(self, creator, folio, checkin, checkout, room,
                           resname, adults=1, children=0):
        # Create Reservation (Special Room)
        reservation = self.env['hotel.reservation'].sudo(creator).create({
            'name': resname,
            'adults': adults,
            'children': children,
            'checkin': checkin.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'checkout': checkout.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'folio_id': folio.id,
            'room_type_id': room.price_room_type.id,
            'product_id': room.product_id.id,
        })
        self.assertTrue(
            reservation,
            "Hotel Calendar can't create a new reservation!")

        # Create Reservation Lines + Update Reservation Price
        days_diff = date_utils.date_diff(checkin, checkout, hours=False)
        res = reservation.sudo(creator).prepare_reservation_lines(
            checkin.strftime(DEFAULT_SERVER_DATETIME_FORMAT), days_diff)
        reservation.sudo(creator).write({
            'reservation_lines': res['commands'],
            'price_unit': res['total_price'],
        })

        return reservation

    @classmethod
    def setUpClass(cls):
        super(TestHotel, cls).setUpClass()

        cls._init_mock_hotel()

        # Restriction Plan
        cls.restriction_1 = cls.env['hotel.room.type.restriction'].create({
            'name': 'Restriction Test #1',
            'active': True
        })

        # Pricelist
        cls.pricelist_1 = cls.env['product.pricelist'].create({
            'name': 'Pricelist Test #1',
        })

        # Minimal Hotel Configuration
        cls.tz_hotel = 'Europe/Madrid'
        cls.default_pricelist_id = cls.pricelist_1.id
        cls.default_restrictions_id = cls.restriction_1.id
        cls.env['ir.values'].sudo().set_default('res.config.settings',
                                                'tz_hotel', cls.tz_hotel)
        cls.env['ir.values'].sudo().set_default('res.config.settings',
                                                'default_pricelist_id',
                                                cls.default_pricelist_id)
        cls.env['ir.values'].sudo().set_default('res.config.settings',
                                                'default_restrictions_id',
                                                cls.default_restrictions_id)

        # User Groups
        user_group_hotel_manager = cls.env.ref('hotel.group_hotel_manager')
        user_group_hotel_user = cls.env.ref('hotel.group_hotel_user')
        user_group_employee = cls.env.ref('base.group_user')
        user_group_public = cls.env.ref('base.group_public')
        user_group_account_inv = cls.env.ref('account.group_account_invoice')
        user_group_sale_manager = cls.env.ref('sales_team.group_sale_manager')
        user_group_base_partner_manager = cls.env.ref(
                                                'base.group_partner_manager')

        # Create Test Users
        Users = cls.env['res.users'].with_context({
            'no_reset_password': True,
            'mail_create_nosubscribe': True
        })
        cls.user_hotel_manager = Users.create({
            'name': 'Jeff Hotel Manager',
            'login': 'hoteljeff',
            'email': 'mynameisjeff@example.com',
            'signature': '--\nJeff',
            'notify_email': 'always',
            'groups_id': [(6, 0, [user_group_hotel_manager.id,
                                  user_group_employee.id,
                                  user_group_account_inv.id,
                                  user_group_sale_manager.id,
                                  user_group_base_partner_manager.id])]
        })
        cls.user_hotel_user = Users.create({
            'name': 'Juancho Hotel User',
            'login': 'juancho',
            'email': 'juancho@example.com',
            'signature': '--\nJuancho',
            'notify_email': 'always',
            'groups_id': [(6, 0, [user_group_hotel_user.id,
                                  user_group_public.id])]
        })

        # Create Tests Records
        RoomTypes = cls.env['hotel.room.type']
        cls.hotel_room_type_simple = RoomTypes.create({
            'name': 'Simple',
            'code_type': 'TSMP',
        })
        cls.hotel_room_type_double = RoomTypes.create({
            'name': 'Double',
            'code_type': 'TDBL',
        })

        VRooms = cls.env['hotel.virtual.room']
        cls.hotel_room_type_budget = VRooms.create({
            'name': 'Budget Room',
            'virtual_code': '001',
            'list_price': 50,
        })
        cls.hotel_room_type_special = VRooms.create({
            'name': 'Special Room',
            'virtual_code': '002',
            'list_price': 150,
        })

        Rooms = cls.env['hotel.room']
        cls.hotel_room_simple_100 = Rooms.create({
            'name': '100',
            'sale_price_type': 'room_type',
            'price_room_type': cls.hotel_room_type_budget.id,
            'categ_id': cls.hotel_room_type_simple.cat_id.id,
            'capacity': 1,
        })
        cls.hotel_room_simple_101 = Rooms.create({
            'name': '101',
            'sale_price_type': 'room_type',
            'price_room_type': cls.hotel_room_type_budget.id,
            'categ_id': cls.hotel_room_type_simple.cat_id.id,
            'capacity': 1,
            'sequence': 1,
        })
        cls.hotel_room_double_200 = Rooms.create({
            'name': '200',
            'sale_price_type': 'room_type',
            'price_room_type': cls.hotel_room_type_special.id,
            'categ_id': cls.hotel_room_type_double.cat_id.id,
            'capacity': 2,
        })

        cls.hotel_room_type_budget.write({
            'room_ids': [(6, False, [cls.hotel_room_simple_100.id,
                                     cls.hotel_room_simple_101.id])],
        })
        cls.hotel_room_type_special.write({
            'room_ids': [(6, False, [cls.hotel_room_double_200.id])],
        })

        # Create a week of fresh data
        now_utc_dt = date_utils.now()
        cls.avails_tmp = {
            cls.hotel_room_type_budget.id: (1, 2, 2, 1, 1, 2, 2),
            cls.hotel_room_type_special.id: (1, 1, 1, 1, 1, 1, 1),
        }
        cls.prices_tmp = {
            cls.hotel_room_type_budget.id: (10.0, 80.0, 80.0, 95.0, 90.0, 80.0,
                                        20.0),
            cls.hotel_room_type_special.id: (5.0, 15.0, 15.0, 35.0, 35.0, 10.0,
                                         10.0),
        }
        cls.restrictions_min_stay_tmp = {
            cls.hotel_room_type_budget.id: (0, 1, 2, 1, 1, 0, 0),
            cls.hotel_room_type_special.id: (3, 1, 0, 2, 0, 1, 4),
        }
        budget_product_id = cls.hotel_room_type_budget.product_id
        special_product_id = cls.hotel_room_type_special.product_id
        product_tmpl_ids = {
            cls.hotel_room_type_budget.id: budget_product_id.product_tmpl_id.id,
            cls.hotel_room_type_special.id: special_product_id.product_tmpl_id.id,
        }
        room_type_avail_obj = cls.env['hotel.room.type.availability']
        room_type_rest_item_obj = cls.env['hotel.room.type.restriction.item']
        pricelist_item_obj = cls.env['product.pricelist.item']
        for k_vr, v_vr in cls.avails_tmp.iteritems():
            for i in range(0, len(v_vr)):
                ndate = now_utc_dt + timedelta(days=i)
                room_type_avail_obj.create({
                    'room_type_id': k_vr,
                    'avail': v_vr[i],
                    'date': ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)
                })
                room_type_rest_item_obj.create({
                    'room_type_id': k_vr,
                    'restriction_id': cls.default_restrictions_id,
                    'date_start': ndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'date_end': ndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'applied_on': '0_room_type',
                    'min_stay': cls.restrictions_min_stay_tmp[k_vr][i],
                })
                pricelist_item_obj.create({
                    'pricelist_id': cls.default_pricelist_id,
                    'date_start': ndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'date_end': ndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'compute_price': 'fixed',
                    'applied_on': '1_product',
                    'product_tmpl_id': product_tmpl_ids[k_vr],
                    'fixed_price': cls.prices_tmp[k_vr][i],
                })
