# Copyright 2017-2018  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HotelServiceLine(models.Model):
    _name = "hotel.service.line"
    _order = "date"

    service_id = fields.Many2one('hotel.service', string='Service Room',
                                 ondelete='cascade', required=True,
                                 copy=False)
    date = fields.Date('Date')
    day_qty = fields.Integer('Units')
    product_id = fields.Many2one(related='service_id.product_id', store=True)

    @api.constrains('day_qty')
    def no_free_resources(self):
        for record in self:
            limit = record.product_id.daily_limit
            if limit > 0:
                out_qty = sum(self.env['hotel.service.line'].search([
                    ('product_id', '=', record.product_id.id),
                    ('date', '=', record.date),
                    ('service_id', '!=', record.service_id.id)
                    ]).mapped('day_qty'))
                if limit < out_qty + record.day_qty:
                    raise ValidationError(
                    _("%s limit exceeded for %s")% (record.service_id.product_id.name,
                                                    record.date))
