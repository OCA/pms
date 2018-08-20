# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
from openerp.exceptions import ValidationError


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    is_channel_pushed = fields.Boolean("WuBook Pushed", default=True, readonly=True,
                                       old_name='wpushed')
    is_daily_plan = fields.Boolean(related='pricelist_id.wdaily', readonly=True,
                                   old_name='wdaily')

    @api.constrains('fixed_price')
    def _check_fixed_price(self):
        vroom_obj = self.env['hotel.virtual.room']
        for record in self:
            vroom = vroom_obj.search([
                ('product_id.product_tmpl_id', '=', record.product_tmpl_id.id)
            ], limit=1)
            if vroom and vroom.channel_room_id and record.compute_price == 'fixed' \
                    and record.fixed_price <= 0.0:
                raise ValidationError(_("Price need be greater than zero"))

    @api.model
    def create(self, vals):
        if self._context.get('channel_action', True):
            pricelist_id = self.env['product.pricelist'].browse(
                vals.get('pricelist_id'))
            vroom = self.env['hotel.virtual.room'].search([
                ('product_id.product_tmpl_id', '=',
                 vals.get('product_tmpl_id')),
                ('channel_room_id', '!=', False)
            ])
            if vroom and pricelist_id.channel_plan_id:
                vals.update({'is_channel_pushed': False})
        return super(ProductPricelistItem, self).create(vals)

    @api.multi
    def write(self, vals):
        if self._context.get('channel_action', True):
            prices_obj = self.env['product.pricelist']
            for record in self:
                pricelist_id = prices_obj.browse(vals.get('pricelist_id')) if \
                        vals.get('pricelist_id') else record.pricelist_id
                product_tmpl_id = vals.get('product_tmpl_id') or \
                        record.product_tmpl_id.id
                vroom = self.env['hotel.virtual.room'].search([
                    ('product_id.product_tmpl_id', '=', product_tmpl_id),
                    ('channel_room_id', '!=', False),
                ])
                if vroom and pricelist_id.channel_plan_id:
                    vals.update({'is_channel_pushed': False})
        return super(ProductPricelistItem, self).write(vals)
