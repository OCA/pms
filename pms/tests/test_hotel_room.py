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
from odoo.exceptions import ValidationError


class TestHotelRoom(TestHotel):

    def test_rooms_by_hotel(self):
        # A room cannot be created in a room type of another hotel
        with self.assertRaises(ValidationError):
            record = self.env['hotel.room'].sudo().create({
                'name': 'Test Room',
                'hotel_id': self.demo_hotel_property.id,
                'room_type_id': self.room_type_0.id,
            })
        # A room cannot be changed to another hotel
        with self.assertRaises(ValidationError):
            self.room_0.sudo().write({
                'hotel_id': self.demo_room_type_0.hotel_id.id
            })

    def test_rooms_by_room_type(self):
        # A room cannot be changed to a room type of another hotel
        with self.assertRaises(ValidationError):
            self.room_0.sudo().write({
                'room_type_id': self.demo_room_type_1.id
            })

    def test_check_capacity(self):
        # The capacity of the room must be greater than 0
        with self.assertRaises(ValidationError):
            self.room_0.sudo().write({
                'capacity': 0
            })
