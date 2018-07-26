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
from odoo.addons.hotel import date_utils
from .common import TestHotelWubook


class TestWubookChannelInfo(TestHotelWubook):

    def test_import_channels_info(self):
        now_utc_dt = date_utils.now()
        day_utc_dt = now_utc_dt + timedelta(days=20)
        info_channel = self.env['wubook.channel.info'].create({
            'wid': 1234,
            'name': 'Test Channel',
        })
        self.assertTrue(info_channel, "Can't create test channel info")
        info_channel.import_channels_info()
