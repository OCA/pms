# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <dev@redneboa.es>
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
from openerp import models, fields, api
from openerp.exceptions import ValidationError


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    wpushed = fields.Boolean("WuBook Pushed", default=True, readonly=True)
    wdaily = fields.Boolean(related='pricelist_id.wdaily', readonly=True)

    @api.constrains('fixed_price')
    def _check_fixed_price(self):
        vroom = self.env['hotel.virtual.room'].search([
                ('product_id.product_tmpl_id', '=', self.product_tmpl_id.id)
            ], limit=1)
        if vroom and vroom.wrid and self.compute_price == 'fixed' \
                and self.fixed_price <= 0.0:
            raise ValidationError(_("Price need be greater than zero"))

    @api.model
    def create(self, vals):
        if self._context.get('wubook_action', True) and \
                self.env['wubook'].is_valid_account():
            pricelist_id = self.env['product.pricelist'].browse(
                                                    vals.get('pricelist_id'))
            vroom = self.env['hotel.virtual.room'].search([
                ('product_id.product_tmpl_id', '=',
                 vals.get('product_tmpl_id')),
                ('wrid', '!=', False)
            ])
            if vroom and pricelist_id.wpid:
                vals.update({'wpushed': False})
        return super(ProductPricelistItem, self).create(vals)

    @api.multi
    def write(self, vals):
        if self._context.get('wubook_action', True) and \
                self.env['wubook'].is_valid_account():
            prices_obj = self.env['product.pricelist']
            for record in self:
                pricelist_id = vals.get('pricelist_id') and \
                        prices_obj.browse(vals.get('pricelist_id')) or \
                        record.pricelist_id
                product_tmpl_id = vals.get('product_tmpl_id') or \
                    record.product_tmpl_id.id
                vroom = self.env['hotel.virtual.room'].search([
                    ('product_id.product_tmpl_id', '=', product_tmpl_id),
                    ('wrid', '!=', False)
                ])
                if vroom and pricelist_id.wpid:
                    vals.update({'wpushed': False})
        return super(ProductPricelistItem, self).write(vals)
