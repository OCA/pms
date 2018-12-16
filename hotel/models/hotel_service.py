# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)


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
    # Non-stored related field to allow portal user to see the image of the product he has ordered
    product_image = fields.Binary('Product Image', related="product_id.image", store=False)
    channel_type = fields.Selection([
        ('door', 'Door'),
        ('mail', 'Mail'),
        ('phone', 'Phone'),
        ('call', 'Call Center'),
        ('web', 'Web')], 'Sales Channel')
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    tax_ids = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)
    currency_id = fields.Many2one(related='folio_id.currency_id', store=True, string='Currency', readonly=True)
    price_subtotal = fields.Monetary(string='Subtotal',
                                     readonly=True,
                                     store=True,
                                     compute='_compute_amount_service')
    price_total = fields.Monetary(string='Total',
                                  readonly=True,
                                  store=True,
                                  compute='_compute_amount_service')
    price_tax = fields.Float(string='Taxes',
                             readonly=True,
                             store=True,
                             compute='_compute_amount_service')

    @api.model
    def create(self, vals):
        vals.update(self._prepare_add_missing_fields(vals))
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

    @api.model
    def _prepare_add_missing_fields(self, values):
        """ Deduce missing required fields from the onchange """
        res = {}
        onchange_fields = ['price_unit','tax_ids']
        if values.get('product_id'):
            line = self.new(values)
            if any(f not in values for f in onchange_fields):
                line.onchange_product_calc_qty()
            for field in onchange_fields:
                if field not in values:
                    res[field] = line._fields[field].convert_to_write(line[field], line)
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

    @api.multi
    def _compute_tax_ids(self):
        for record in self:
            # If company_id is set, always filter taxes by the company
            folio = record.folio_id or self.env.context.get('default_folio_id')
            record.tax_id = record.product_id.taxes_id.filtered(lambda r: not record.company_id or r.company_id == folio.company_id)

    @api.multi
    def _get_display_price(self, product):
        folio = self.folio_id or self.env.context.get('default_folio_id')
        if folio.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=folio.pricelist_id.id).price
        product_context = dict(self.env.context, partner_id=folio.partner_id.id, date=folio.date_order, uom=self.product_id.uom_id.id)
        final_price, rule_id = folio.pricelist_id.with_context(product_context).get_product_price_rule(self.product_id, self.product_qty or 1.0, folio.partner_id)
        base_price, currency_id = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.product_qty, product_id.uom_id, folio.pricelist_id.id)
        if currency_id != folio.pricelist_id.currency_id.id:
            base_price = self.env['res.currency'].browse(currency_id).with_context(product_context).compute(base_price, folio.pricelist_id.currency_id)
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    @api.onchange('product_id')
    def onchange_product_calc_qty(self):
        """
        Compute the default quantity according to the
        configuration of the selected product, in per_day product configuration,
        the qty is autocalculated and readonly based on service_lines qty
        """
        if not self.product_id:
            return
        vals = {}
        vals['product_qty'] = 1.0
        for record in self:
            if record.per_day and record.ser_room_line:
                product = record.product_id
                reservation = record.ser_room_line
                vals.update(record.prepare_service_lines(
                        dfrom=reservation.checkin,
                        days=reservation.nights,
                        per_person=product.per_person,
                        persons=reservation.adults,
                        old_line_days=record.service_line_ids))
                if record.product_id.daily_limit > 0:
                    for day in record.service_line_ids:
                        day.no_free_resources()
        """
        Compute tax and price unit
        """
        self._compute_tax_ids()
        vals['price_unit'] = self._compute_price_unit()
        record.update(vals)

    @api.multi
    def _compute_price_unit(self):
        self.ensure_one()
        folio = self.folio_id or self.env.context.get('default_folio_id')
        reservation = self.ser_room_line or self.env.context.get('ser_room_line')
        partner = folio.partner_id if folio else reservation.partner_id
        pricelist = folio.pricelist_id if folio else reservation.pricelist_id
        if reservation and self.is_board_service:
            board_room_type = reservation.board_service_room_id
            if board_room_type.price_type == 'fixed':
                return self.env['hotel.board.service.room.type.line'].search([
                    ('hotel_board_service_room_type_id', '=', board_room_type.id),
                    ('product_id','=',self.product_id.id)]).amount
            else:
                return (reservation.price_total * self.env['hotel.board.service.room.type.line'].search([
                    ('hotel_board_service_room_type_id', '=', board_room_type.id),
                    ('product_id','=',self.product_id.id)]).amount) / 100
        else:
            product = self.product_id.with_context(
                    lang=partner.lang,
                    partner=partner.id,
                    quantity=self.product_qty,
                    date=folio.date_order or fields.Date.today(),
                    pricelist=pricelist.id,
                    uom=self.product_id.uom_id.id,
                    fiscal_position=False
                )
            return self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_ids, folio.company_id)
            
         

    @api.model
    def prepare_service_lines(self, **kwargs):
        """
        Prepare line and respect the old manual changes on lines
        """
        cmds = [(5, 0, 0)]
        old_line_days = kwargs.get('old_line_days')
        total_qty = 0
        day_qty = 1
        if kwargs.get('per_person'): #WARNING: Change adults in reservation NOT update qty service!!
            day_qty = kwargs.get('persons')
        for i in range(0, kwargs.get('days')):
            idate = (fields.Date.from_string(kwargs.get('dfrom')) + timedelta(days=i)).strftime(
                DEFAULT_SERVER_DATE_FORMAT)
            if not old_line_days or idate not in old_line_days.mapped('date'):
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

    @api.depends('product_qty', 'discount', 'price_unit', 'tax_ids')
    def _compute_amount_service(self):
        """
        Compute the amounts of the service line.
        """
        for record in self:
            folio = record.folio_id or self.env.context.get('default_folio_id')
            reservation = record.ser_room_line or self.env.context.get('ser_room_line')
            currency = folio.currency_id if folio else reservation.currency_id
            product = record.product_id
            price = record.price_unit * (1 - (record.discount or 0.0) * 0.01)
            taxes = record.tax_ids.compute_all(price, currency, record.product_qty, product=product)
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

    @api.multi
    def open_service_lines(self):
        action = self.env.ref('hotel.action_hotel_services_form').read()[0]
        action['views'] = [(self.env.ref('hotel.hotel_service_view_form').id, 'form')]
        action['res_id'] = self.id
        action['target'] = 'new'
        return action
    
    #~ @api.constrains('product_qty')
    #~ def constrains_qty_per_day(self):
        #~ for record in self:
            #~ if record.per_day:
                #~ service_lines = self.env['hotel.service_line']
                #~ total_day_qty = sum(service_lines.with_context({'service_id': record.id}).mapped('day_qty'))
                #~ if record.product_qty != total_day_qty:
                    #~ raise ValidationError (_('The quantity per line and per day does not correspond'))
