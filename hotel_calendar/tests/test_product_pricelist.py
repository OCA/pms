# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018 Alexandre Díaz <dev@redneboa.es>
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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from .common import TestHotelCalendar
from odoo.addons.hotel import date_utils


class TestProductPricelist(TestHotelCalendar):

    def test_update_price(self):
        now_utc_dt = date_utils.now()
        now_utc_str = now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)

        room_type_tmpl_id = self.hotel_room_type_special.product_id.product_tmpl_id

        pritem_obj = self.env['product.pricelist.item']
        plitem = pritem_obj.search([
            ('pricelist_id', '=', self.default_pricelist_id),
            ('product_tmpl_id', '=', room_type_tmpl_id.id),
            ('date_start', '=', now_utc_str),
            ('date_end', '=', now_utc_str),
            ('applied_on', '=', '1_product'),
            ('compute_price', '=', 'fixed')
        ])
        old_price = plitem.fixed_price

        self.pricelist_1.update_price(
            self.hotel_room_type_special.id,
            now_utc_str,
            999.9)

        plitem = pritem_obj.search([
            ('pricelist_id', '=', self.default_pricelist_id),
            ('product_tmpl_id', '=', room_type_tmpl_id.id),
            ('date_start', '=', now_utc_str),
            ('date_end', '=', now_utc_str),
            ('applied_on', '=', '1_product'),
            ('compute_price', '=', 'fixed')
        ])
        new_price = plitem.fixed_price

        self.assertNotEqual(old_price,
                            new_price,
                            "Hotel Calendar can't change price")
        self.assertEqual(new_price,
                         999.9,
                         "Hotel Calendar can't change price")
