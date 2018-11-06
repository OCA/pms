# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import time
import logging
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
_logger = logging.getLogger(__name__)

class HotelService(models.Model):
    _name = 'hotel.service'
    _description = 'Hotel Services and its charges'

    @api.model
    def _default_ser_room_line(self):
        if 'room_lines' in self.env.context and self.env.context['room_lines']:
            ids = [item[1] for item in self.env.context['room_lines']]
            return self.env['hotel.reservation'].search([
                ('id', 'in', ids),
            ], limit=1)
        return False

    name = fields.Char('Service description')
    product_id = fields.Many2one('product.product', 'Service',
                                 required=True)
    folio_id = fields.Many2one('hotel.folio', 'Folio',
                               ondelete='cascade')
    ser_room_line = fields.Many2one('hotel.reservation', 'Room',
                                    default=_default_ser_room_line)
    service_line_ids = fields.One2many('hotel.service.line',
                                       'service_id')
    product_qty = fields.Integer('Quantity')
    pricelist_id = fields.Many2one(
        related='folio_id.pricelist_id')
    channel_type = fields.Selection([
        ('door', 'Door'),
        ('mail', 'Mail'),
        ('phone', 'Phone'),
        ('call', 'Call Center'),
        ('web', 'Web')], 'Sales Channel')
    currency_id = fields.Many2one('res.currency',
                                  related='pricelist_id.currency_id',
                                  string='Currency', readonly=True, required=True)
    price_subtotal = fields.Monetary(string='Subtotal',
                                     readonly=True,
                                     store=True,
                                     compute='_compute_amount_reservation')
    price_total = fields.Monetary(string='Total',
                                  readonly=True,
                                  store=True,
                                  compute='_compute_amount_reservation')
    price_tax = fields.Float(string='Taxes',
                             readonly=True,
                             store=True,
                             compute='_compute_amount_reservation')

    @api.onchange('product_id')
    def onchange_product_calc_qty(self):
        """
        Compute the default quantity according to the
        configuration of the selected product
        """
        for record in self:
            product = record.product_id
            reservation = record.ser_room_line
            if product and reservation:
                qty = 1
                if product.per_day:
                    qty = qty * reservation.nights
                if product.per_person:
                    qty = qty * (reservation.adults + reservation.children)
                record.product_qty = qty

    @api.onchange('product_qty')
    def onchange_product_qty_days_selection(self):
        """
        Try to calculate the days on which the product
        should be served as long as the product is per day
        """
        for record in self:
            reservation = record.ser_room_line
            if record.product_id.per_day:
                days_diff = (
                fields.Date.from_string(reservation.checkout) - fields.Date.from_string(reservation.checkin)
                ).days
                record.update(record.prepare_service_lines(
                reservation.checkin,
                days_diff))
            else:
                record.update(rec.prepare_service_lines(
                reservation.checkin, 1))
                

    @api.multi
    def prepare_service_lines(self, dfrom, days, vals=False):
        self.ensure_one()
        old_qty = 0
        cmds = [(5, 0, 0)]
        if not vals:
            vals
        product = vals.get('product_id') or self.product_id
        old_lines_days = self.mapped('service_line_ids.date')
        for day in service_line_ids:
            old_qty = old_qty + day.day_qty
        qty_day = (self.product_qty - old_qty) // (days - count(old_line_days))
        rest_day = (self.product_qty - old_qty) % (days - count(old_line_days))
        reservation = rec.ser_room_line
        for i in range(0, days):
            idate = (fields.Date.from_string(dfrom) + timedelta(days=i)).strftime(
                DEFAULT_SERVER_DATE_FORMAT)
            old_line = self.service_line_ids.filtered(lambda r: r.date == idate)
            if idate not in old_lines_days:
                cmds.append((0, False, {
                    'date': idate,
                    'day_qty': qty
                }))
            else:
                cmds.append((4, old_line.id))
        return {'service_line_ids': cmds}

    @api.depends('qty_product', 'tax_id')
    def _compute_amount_service(self):
        """
        Compute the amounts of the service line.
        """
        for record in self:           
            product = rec.product_id
            price = amount_room * (1 - (record.discount or 0.0) * 0.01)
            taxes = record.tax_id.compute_all(price, record.currency_id, 1, product=product)
            record.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
    
                
