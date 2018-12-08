# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
from odoo.exceptions import ValidationError

class HotelService(models.Model):
    _name = 'hotel.service'
    _description = 'Hotel Services and its charges'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        if not(name == '' and operator == 'ilike'):
            args += [
                '|',
                ('ser_room_line.name', operator, name),
                ('name', operator, name)
            ]
        return super(HotelService, self).name_search(
            name='', args=args, operator='ilike', limit=limit)

    @api.multi
    def name_get(self):
        result = []
        for res in self:
            name = u'%s (%s)' % (res.name, res.ser_room_line.name)
            result.append((res.id, name))
        return result


    @api.model
    def _default_ser_room_line(self):
        if self.env.context.get('room_lines'):
            ids = [item[1] for item in self.env.context['room_lines']]
            return self.env['hotel.reservation'].browse([
                (ids)], limit=1)
        return False

    name = fields.Char('Service description')
    product_id = fields.Many2one('product.product', 'Service', required=True)
    folio_id = fields.Many2one('hotel.folio', 'Folio', ondelete='cascade')
    ser_room_line = fields.Many2one('hotel.reservation', 'Room',
                                    default=_default_ser_room_line)
    per_day = fields.Boolean(related='product_id.per_day')
    service_line_ids = fields.One2many('hotel.service.line', 'service_id')
    product_qty = fields.Integer('Quantity')
    days_qty = fields.Integer(compute="_compute_days_qty", store=True)
    is_board_service = fields.Boolean()
    pricelist_id = fields.Many2one(related='folio_id.pricelist_id')
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

    @api.model
    def create(self, vals):
        if self.compute_lines_out_vals(vals):
            reservation = self.env['hotel.reservation'].browse(vals['ser_room_line'])
            product = self.env['product.product'].browse(vals['product_id'])
            
            vals.update(self.prepare_service_lines(
                dfrom=reservation.checkin,
                days=reservation.nights,
                per_person=product.per_person,
                persons=reservation.adults,
                old_day_lines=False,
                ))
        record = super(HotelService, self).create(vals)
        return record

    @api.multi
    def write(self, vals):
        #If you write product, We must check if its necesary create or delete
        #service lines
        if vals.get('product_id'):
            product = self.env['product.product'].browse(vals.get('product_id'))
            if not product.per_day:
                vals.update({
                    'service_line_ids' : [(5, 0, 0)]
                    })
            else:
                for record in self:
                    reservations = self.env['hotel.reservation']
                    reservation = reservations.browse(vals['ser_room_line']) \
                        if 'ser_room_line' in vals else record.ser_room_line
                    record.update(record.prepare_service_lines(
                        dfrom=reservation.checkin,
                        days=reservation.nights,
                        per_person=product.per_person,
                        persons=reservation.adults,
                        old_line_days=self.service_line_ids
                        ))
        res = super(HotelService, self).write(vals)
        return res

    @api.multi
    def compute_lines_out_vals(self, vals):
        """
        Compute if It is necesary service days in write/create
        """
        if not vals:
            vals = {}
        if 'product_id' in vals:
            product = self.env['product.product'].browse(vals['product_id']) \
                if 'product_id' in vals else self.product_id
            if (product.per_day and 'service_line_ids' not in vals):
                return True
        return False

    @api.onchange('product_id')
    def onchange_product_calc_qty(self):
        """
        Compute the default quantity according to the
        configuration of the selected product, in per_day product configuration,
        the qty is autocalculated and readonly based on service_lines qty
        """
        for record in self:
            if record.per_day and record.ser_room_line:
                product = record.product_id
                reservation = record.ser_room_line
                record.update(self.prepare_service_lines(
                        dfrom=reservation.checkin,
                        days=reservation.nights,
                        per_person=product.per_person,
                        persons=reservation.adults,
                        old_line_days=self.service_line_ids))
                if record.product_id.daily_limit > 0:
                    for day in record.service_line_ids:
                        day.no_free_resources()

    @api.model
    def prepare_service_lines(self, **kwargs):
        """
        Prepare line and respect the old manual changes on lines
        """
        cmds = [(5, 0, 0)]
        old_lines_days = kwargs.get('old_lines_days')
        total_qty = 0
        day_qty = 1
        if kwargs.get('per_person'): #WARNING: Change adults in reservation NOT update qty service!!
            day_qty = kwargs.get('persons')
        old_line_days = self.env['hotel.service.line'].browse(kwargs.get('old_line_days'))
        for i in range(0, kwargs.get('days')):
            idate = (fields.Date.from_string(kwargs.get('dfrom')) + timedelta(days=i)).strftime(
                DEFAULT_SERVER_DATE_FORMAT)
            if not old_lines_days or idate not in old_lines_days.mapped('date'):
                cmds.append((0, False, {
                    'date': idate,
                    'day_qty': day_qty
                }))
                total_qty = total_qty + day_qty
            else:
                old_line = old_line_days.filtered(lambda r: r.date == idate)
                cmds.append((4, old_line.id))
                total_qty = total_qty + old_line.day_qty
        return {'service_line_ids': cmds, 'product_qty': total_qty}

    @api.depends('qty_product', 'tax_id')
    def _compute_amount_service(self):
        """
        Compute the amounts of the service line.
        """
        for record in self:
            product = record.product_id
            price = amount_room * (1 - (record.discount or 0.0) * 0.01)
            taxes = record.tax_id.compute_all(price, record.currency_id, 1, product=product)
            record.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.depends('service_line_ids.day_qty')
    def _compute_days_qty(self):
        for record in self:
            if record.per_day:
                qty = sum(record.service_line_ids.mapped('day_qty'))
                vals = {
                    'days_qty': qty,
                    'product_qty': qty
                    }
            else:
                vals = {'days_qty': 0}
            record.update(vals)
    
    @api.constrains('qty_product')
    def constrains_qty_per_day(self):
        for record in self:
            if record.per_day:
                service_lines = self.env['hotel.service_line']
                total_day_qty = sum(service_lines.with_context({'service_id': record.id}).mapped('day_qty'))
                if record.qty_product != total_day_qty:
                    raise ValidationError (_('The quantity per line and per day does not correspond'))
