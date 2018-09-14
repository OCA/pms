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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.addons.hotel import date_utils
from .common import TestHotelWubook
import logging
_logger = logging.getLogger(__name__)


class TestProductPricelistItem(TestHotelWubook):

    def test_create(self):
        now_utc_dt = date_utils.now()
        day_utc_dt = now_utc_dt + timedelta(days=20)
        budget_product_id = self.hotel_room_type_budget.product_id
        pr_item_obj = self.env['product.pricelist.item']

        parity_pricelist = self.env['product.pricelist'].browse([
                                                    self.parity_pricelist_id])
        parity_pricelist.write({'wpid': 1234})
        pricelist_item = pr_item_obj.sudo(self.user_hotel_manager).create({
            'pricelist_id': self.parity_pricelist_id,
            'date_start': day_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            'date_end': day_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            'compute_price': 'fixed',
            'applied_on': '1_product',
            'product_tmpl_id': budget_product_id.product_tmpl_id.id,
            'fixed_price': 99.0,
        })
        self.assertTrue(pricelist_item, "Can't create test pricelist")
        self.assertFalse(pricelist_item.wpushed, "Invalid pushed status")

    def test_write(self):
        now_utc_dt = date_utils.now()
        day_utc_dt = now_utc_dt + timedelta(days=20)
        budget_product_id = self.hotel_room_type_budget.product_id
        pr_item_obj = self.env['product.pricelist.item']

        parity_pricelist = self.env['product.pricelist'].browse([
                                                    self.parity_pricelist_id])
        parity_pricelist.write({'wpid': 1234})
        pricelist_item = pr_item_obj.sudo(self.user_hotel_manager).create({
            'pricelist_id': self.parity_pricelist_id,
            'date_start': day_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            'date_end': day_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            'compute_price': 'fixed',
            'applied_on': '1_product',
            'product_tmpl_id': budget_product_id.product_tmpl_id.id,
            'fixed_price': 99.0,
        })
        self.assertTrue(pricelist_item, "Can't create test pricelist")

        pricelist_item.write({'fixed_price': 30.0})
        self.assertEqual(pricelist_item.fixed_price, 30.0, "Invalid price")
