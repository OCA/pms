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
from .common import TestHotel
from psycopg2 import IntegrityError
from odoo.tools import mute_logger


class TestHotelRoomType(TestHotel):

    # TODO: use users with different access rules

    # code type must be unique by hotel
    def test_code_type_unique_by_hotel(self):
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            self.room_type_0.sudo().write({
                'code_type': self.room_type_1.code_type
            })

    # code type can be used in other hotel
    def test_code_type_shared_by_hotel(self):
        test_result = self.demo_room_type_0.sudo().write({
            'code_type': self.room_type_0.code_type
        })
        self.assertEqual(test_result, True)

