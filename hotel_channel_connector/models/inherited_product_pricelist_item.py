# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    is_channel_pushed = fields.Boolean("WuBook Pushed", default=True, readonly=True,
                                       old_name='wpushed')
    is_daily_plan = fields.Boolean(related='pricelist_id.channel_bind_ids.is_daily_plan', readonly=True,
                                   old_name='wdaily')

    @api.constrains('fixed_price')
    def _check_fixed_price(self):
        room_type_obj = self.env['hotel.room.type']
        for record in self:
            room_type = room_type_obj.search([
                ('product_id.product_tmpl_id', '=', record.product_tmpl_id.id)
            ], limit=1)
            if room_type and room_type.channel_room_id and record.compute_price == 'fixed' \
                    and record.fixed_price <= 0.0:
                raise ValidationError(_("Price need be greater than zero"))

    @api.model
    def create(self, vals):
        if self._context.get('channel_action', True):
            pricelist_id = self.env['product.pricelist'].browse(
                vals.get('pricelist_id'))
            room_type = self.env['hotel.room.type'].search([
                ('product_id.product_tmpl_id', '=',
                 vals.get('product_tmpl_id')),
                ('channel_room_id', '!=', False)
            ])
            if room_type and pricelist_id.channel_plan_id:
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
                room_type = self.env['hotel.room.type'].search([
                    ('product_id.product_tmpl_id', '=', product_tmpl_id),
                    ('channel_room_id', '!=', False),
                ])
                if room_type and pricelist_id.channel_plan_id:
                    vals.update({'is_channel_pushed': False})
        return super(ProductPricelistItem, self).write(vals)
