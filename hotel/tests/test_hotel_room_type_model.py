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
from .common import TestHotel
from odoo.exceptions import ValidationError

class TestHotelRoomType(TestHotel):

    def test_change_room_ids(self):

        # Avoid the unconscious change of room type_id from room_type
        #TODO: use sudo users hotel
        with self.assertRaises(ValidationError):
            cls.room_type_0.sudo().write({
                'room_ids':(4, cls.room_type_3.id)
            })
