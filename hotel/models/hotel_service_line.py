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
    price_total = fields.Float('Price Total',
                               compute='_compute_price_total',
                               store=True)
    price_unit = fields.Float('Unit Price',
                              related="service_id.price_unit",
                              readonly=True,
                              store=True)
    room_id = fields.Many2one(strin='Room',
                              related="service_id.ser_room_line",
                              readonly=True,
                              store=True)
    discount = fields.Float('Discount',
                            related="service_id.discount",
                            readonly=True,
                            store=True)
    cancel_discount = fields.Float('Discount', compute='_compute_cancel_discount')
    tax_ids = fields.Many2many('account.tax',
                               string='Taxes',
                               related="service_id.tax_ids",
                               readonly="True")

    def _cancel_discount(self):
        for record in self:
            if record.reservation_id:
                day = record.reservation_id.reservation_line_ids.filtered(
                    lambda d: d.date == record.date
                )
                record.cancel_discount = day.cancel_discount

    @api.depends('day_qty', 'service_id.price_total')
    def _compute_price_total(self):
        """
        Used to reports
        """
        for record in self:
            if record.service_id.product_qty != 0:
                record.price_total = (record.service_id.price_total * record.day_qty) / record.service_id.product_qty
            else:
                record.price_total = 0

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
