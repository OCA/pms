# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class HotelCancelationRule(models.Model):
    _name = 'hotel.cancelation.rule'
    _description = 'Cancelation Rules'

    name = fields.Char('Amenity Name', translate=True, required=True)
    active = fields.Boolean('Active', default=True)
    pricelist_ids = fields.One2many('product.pricelist',
                                    'cancelation_rule_id',
                                    'Pricelist that use this rule')
    days_intime = fields.Integer(
        'Days Late',
        help='Maximum number of days for free cancellation before Checkin')
    penalty_late = fields.Integer('% Penalty Late', defaul="100")
    apply_on_late = fields.Selection([
        ('first', 'First Day'),
        ('all', 'All Days'),
        ('days', 'Specify days')], 'Late apply on', default='first')
    days_late = fields.Integer('Late first days', default="2")
    penalty_noshow = fields.Integer('% Penalty No Show', default="100")
    apply_on_noshow = fields.Selection([
        ('first', 'First Day'),
        ('all', 'All Days'),
        ('days', 'Specify days')], 'No Show apply on', default='all')
    days_noshow = fields.Integer('NoShow first days', default="2")
