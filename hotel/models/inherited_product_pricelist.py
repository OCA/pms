# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    is_staff = fields.Boolean('Is Staff')

    pricelist_type = fields.Selection([
        ('daily', 'Daily Plan'),
    ], string='Pricelist Type', default='daily')
    cancelation_rule_id = fields.Many2one(
        'hotel.cancelation.rule',
        string="Cancelation Policy")

    @api.multi
    @api.depends('name')
    def name_get(self):
        pricelist_id = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_pricelist_id')
        if pricelist_id:
            pricelist_id = int(pricelist_id)
        org_names = super(ProductPricelist, self).name_get()
        names = []
        for name in org_names:
            if name[0] == pricelist_id:
                names.append((name[0], '%s (Default)' % name[1]))
            else:
                names.append((name[0], name[1]))
        return names
