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
from odoo.tools import (
    DEFAULT_SERVER_DATETIME_FORMAT,
    DEFAULT_SERVER_DATE_FORMAT)
from odoo.exceptions import AccessError
from .common import TestChannelConnectorWubook


class TestChannelRoomType(TestChannelConnectorWubook):

    def create_room(self, shortcode, name, capacity, price, availability, defboard, rtype):
        return True

    def fetch_rooms(self):
        return True

    def modify_room(self, channel_room_id, name, capacity, price, availability, scode, defboard, rtype):
        import wdb; wdb.set_trace()
        self.hotel_room_type_simple.ota_capacity = 1
        return True

    def delete_room(self, channel_room_id):
        return True

    # def test_get_capacity(self):
    #     self.assertEqual(self.room_type_0.wcapacity,
    #                      1,
    #                      "Invalid wcapacity")

    # def test_check_wcapacity(self):
    #     with self.assertRaises(ValidationError):
    #         self.room_type_0.sudo(self.user_hotel_manager).write({
    #             'wcapacity': 0
    #         })

    # def test_check_wscode(self):
    #     with self.assertRaises(ValidationError):
    #         self.room_type_0.sudo(self.user_hotel_manager).write({
    #             'wscode': 'abcdefg'
    #         })

    # def test_get_restrictions(self):
    #     now_utc_dt = date_utils.now()
    #     rests = self.hotel_room_type_budget.sudo(
    #                                 self.user_hotel_manager).get_restrictions(
    #                                     now_utc_dt.strftime(
    #                                         DEFAULT_SERVER_DATE_FORMAT))
    #     self.assertTrue(any(rests), "Restrictions not found")

    # def test_import_rooms(self):
    #     self.room_type_0.sudo(self.user_hotel_manager).import_rooms()

    # def test_create(self):
    #     room_type_obj = self.env['hotel.room.type']
    #     room_type = room_type_obj.sudo(self.user_hotel_manager).create({
    #         'name': 'Budget Room',
    #         'virtual_code': '001',
    #         'list_price': 50,
    #         'wrid': 1234
    #     })
    #     room_type.unlink()

    # def test_unlink(self):
    #     with self.assertRaises(AccessError):
    #         self.hotel_room_type_simple.sudo(self.manager_hotel_demo).unlink()
