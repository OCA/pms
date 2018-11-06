# Copyright 2017-2018  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields
from odoo.addons import decimal_precision as dp

class HotelServiceLine(models.Model):
    _name = "hotel.service.line"
    _order = "date"

    service_id = fields.Many2one('hotel.service', string='Service',
                                     ondelete='cascade', required=True,
                                     copy=False)
    date = fields.Date('Date')
    day_qty = fields.Integer('Units')
    product_id = fields.Many2one(related='service_id.product_id')

    @api.constrains('day_qty')
    def no_free_resources(self):
        for record in self:
            limit = record.product_id.daily_limit
            if limit > 0:
                out_qty = sum(self.env['hotel.service.line'].search([(
                    'product_id','=',record.product_id,
                    'date','=',record.date)]).mapped('day_qty'))
                if limit < out_qty + record.day_qty:
                    raise ValidationError(
                    _("Limit exceeded for %s")% record.date)
                    

                
        
