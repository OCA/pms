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


class TestProductPricelist(TestHotelWubook):

    def test_get_wubook_prices(self):
        default_pricelist = self.env['product.pricelist'].browse([
                                                    self.default_pricelist_id])
        wprices = default_pricelist.sudo(
                                self.user_hotel_manager).get_wubook_prices()
        self.assertTrue(any(wprices), "Can't get any price for wubook")

    def test_create(self):
        npricelist = self.env['product.pricelist'].sudo(
            self.user_hotel_manager).create({
                'name': 'Pricelist Test #1'
            })
        self.assertTrue(npricelist, "Can't create test pricelist")

    def test_write(self):
        default_pricelist = self.env['product.pricelist'].browse([
                                                    self.default_pricelist_id])
        default_pricelist.sudo(self.user_hotel_manager).write({
            'name': 'Pricelist Test New Name #1'
        })
        self.assertEqual(
            default_pricelist.name,
            'Pricelist Test New Name #1',
            'Invalid pricelist name')

    def test_unlink(self):
        default_pricelist = self.env['product.pricelist'].browse([
                                                    self.default_pricelist_id])
        default_pricelist.sudo(self.user_hotel_manager).unlink()

    def test_import_price_plans(self):
        default_pricelist = self.env['product.pricelist'].browse([
                                                    self.default_pricelist_id])
        default_pricelist.import_price_plans()

    def test_name_get(self):
        default_pricelist = self.env['product.pricelist'].browse([
                                                    self.default_pricelist_id])
        rest_name = default_pricelist.sudo(self.user_hotel_manager).name_get()
        self.assertTrue('WuBook' in rest_name[0][1], 'Invalid Name')
        default_pricelist.sudo(self.user_hotel_manager).write({'wpid': ''})
        rest_name = default_pricelist.sudo(self.user_hotel_manager).name_get()
        self.assertFalse('WuBook' in rest_name[0][1], 'Invalid Name')
