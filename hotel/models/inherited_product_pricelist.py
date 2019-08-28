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

    hotel_ids = fields.Many2many('hotel.property', string='Hotels', required=False,
                                 ondelete='restrict')

