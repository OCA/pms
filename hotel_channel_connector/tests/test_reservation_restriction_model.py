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
from .common import TestHotelWubook
import logging
_logger = logging.getLogger(__name__)


class TestReservationRestriction(TestHotelWubook):

    def test_get_wubook_restrictions(self):
        wrests = self.restriction_1.sudo(self.user_hotel_manager).\
            get_wubook_restrictions()
        self.assertTrue(any(wrests), "Any restriction found")

    def test_create(self):
        vroo_restriction_obj = self.env['hotel.virtual.room.restriction']
        # Restriction Plan
        restriction = vroo_restriction_obj.sudo(self.user_hotel_manager).\
            create({
                'name': 'Restriction Test #1',
                'active': True
            })
        self.assertTrue(restriction, "Can't create new restriction")

    def test_write(self):
        vroo_restriction_obj = self.env['hotel.virtual.room.restriction']
        # Restriction Plan
        restriction = vroo_restriction_obj.sudo(self.user_hotel_manager).\
            create({
                'name': 'Restriction Test #1',
                'active': True
            })
        self.assertTrue(restriction, "Can't create new restriction")
        restriction.sudo(self.user_hotel_manager).write({
            'name': 'Restriction Test Modif #1'
        })
        self.assertEqual(
            restriction.name,
            'Restriction Test Modif #1',
            "Can't modif restriction")

    def test_unlink(self):
        vroo_restriction_obj = self.env['hotel.virtual.room.restriction']
        # Restriction Plan
        restriction = vroo_restriction_obj.sudo(self.user_hotel_manager).\
            create({
                'name': 'Restriction Test #1',
                'active': True,
                'wpid': 1234,
            })
        self.assertTrue(restriction, "Can't create new restriction")
        restriction.sudo(self.user_hotel_manager).unlink()

    def test_import_restriction_plans(self):
        vroo_restriction_obj = self.env['hotel.virtual.room.restriction']
        # Restriction Plan
        restriction = vroo_restriction_obj.sudo(self.user_hotel_manager).\
            create({
                'name': 'Restriction Test #1',
                'active': True,
                'wpid': 1234,
            })
        self.assertTrue(restriction, "Can't create new restriction")
        restriction.sudo(self.user_hotel_manager).import_restriction_plans()

    def test_name_get(self):
        vroo_restriction_obj = self.env['hotel.virtual.room.restriction']
        # Restriction Plan
        restriction = vroo_restriction_obj.sudo(self.user_hotel_manager).\
            create({
                'name': 'Restriction Test #1',
                'active': True,
            })
        self.assertTrue(restriction, "Can't create new restriction")
        rest_name = restriction.sudo(self.user_hotel_manager).name_get()
        self.assertTrue('WuBook' in rest_name[0][1], 'Invalid Name')
        restriction.sudo(self.user_hotel_manager).write({'wpid': ''})
        rest_name = restriction.sudo(self.user_hotel_manager).name_get()
        self.assertFalse('WuBook' in rest_name[0][1], 'Invalid Name')
