# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.hotel import date_utils


class IrDefault(models.Model):
    _inherit = 'ir.default'

    @api.model
    def set(self, model_name, field_name, value, user_id=False, company_id=False, condition=False):
        super(IrDefault, self).set(model_name, field_name, value, user_id, company_id, condition)
        if model_name == 'res.config.settings' and field_name == 'parity_pricelist_id':
            pricelist_id = int(value)
            self.env['virtual.room.pricelist.cached'].search([]).unlink()

            pricelist_items = self.env['product.pricelist.item'].search([
                ('pricelist_id', '=', pricelist_id)
            ])
            vroom_obj = self.env['hotel.room.type']
            vroom_pr_cached_obj = self.env['virtual.room.pricelist.cached']
            for pitem in pricelist_items:
                date_start = pitem.date_start
                product_tmpl_id = pitem.product_tmpl_id.id
                fixed_price = pitem.fixed_price
                vroom = vroom_obj.search([
                    ('product_id.product_tmpl_id', '=', product_tmpl_id),
                    ('date_start', '>=', date_utils.now().strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT))
                ], limit=1)
                vroom_pr_cached_obj.create({
                    'virtual_room_id': vroom.id,
                    'date': date_start,
                    'price': fixed_price,
                })
