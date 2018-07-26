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
from .common import TestHotelWubook
from openerp.exceptions import ValidationError
from odoo.addons.hotel import date_utils
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class TestVirtualRoomAvailability(TestHotelWubook):

    def test_write(self):
        now_utc_dt = date_utils.now()
        day_utc_dt = now_utc_dt + timedelta(days=1)
        vroom_avail_obj = self.env['hotel.virtual.room.availability']
        avail = vroom_avail_obj.search([
            ('virtual_room_id', '=', self.hotel_vroom_budget.id),
            ('date', '=', now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT))
        ], limit=1)
        avail.write({
            'avail': 1,
        })
        self.assertEqual(avail.avail, 1, "Invalid avail")
