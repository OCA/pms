# -*- coding: utf-8 -*-
# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import except_orm, UserError, ValidationError
from odoo.tools import (
    misc,
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
from odoo import models, fields, api, _
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from dateutil import tz
from datetime import datetime, timedelta, date
from odoo.addons.hotel import date_utils
import pytz
import time
import logging
_logger = logging.getLogger(__name__)

from odoo.addons import decimal_precision as dp

class HotelReservation(models.Model):

    def _get_default_checkin(self):
        folio = False
        if 'folio_id' in self._context:
            folio = self.env['hotel.folio'].search([
                ('id', '=', self._context['folio_id'])
            ])
        if folio and folio.room_lines:
            return folio.room_lines[0].checkin
        else:
            tz_hotel = self.env['ir.default'].sudo().get(
                'res.config.settings', 'tz_hotel')
            today = fields.Date.context_today(self.with_context(tz=tz_hotel))
            return fields.Date.from_string(today).strftime(DEFAULT_SERVER_DATE_FORMAT)

    def _get_default_checkout(self):
        folio = False
        if 'folio_id' in self._context:
            folio = self.env['hotel.folio'].search([
                ('id', '=', self._context['folio_id'])
            ])
        if folio and folio.room_lines:
            return folio.room_lines[0].checkout
        else:
            tz_hotel = self.env['ir.default'].sudo().get(
                'res.config.settings', 'tz_hotel')
            today = fields.Date.context_today(self.with_context(tz=tz_hotel))
            return (fields.Date.from_string(today) + timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT)

    def _get_default_arrival_hour(self):
        folio = False
        default_arrival_hour = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_arrival_hour')
        if 'folio_id' in self._context:
            folio = self.env['hotel.folio'].search([
                ('id', '=', self._context['folio_id'])
            ])
        if folio and folio.room_lines:
            return folio.room_lines[0].arrival_hour
        else:
            return default_arrival_hour

    def _get_default_departure_hour(self):
        folio = False
        default_departure_hour = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_departure_hour')
        if 'folio_id' in self._context:
            folio = self.env['hotel.folio'].search([
                ('id', '=', self._context['folio_id'])
            ])
        if folio and folio.room_lines:
            return folio.room_lines[0].departure_hour
        else:
            return default_departure_hour

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        if not(name == '' and operator == 'ilike'):
            args += [
                '|',
                ('folio_id.name', operator, name),
                ('room_id.name', operator, name)
            ]
        return super(HotelReservation, self).name_search(
            name='', args=args, operator='ilike', limit=limit)

    @api.multi
    def name_get(self):
        result = []
        for res in self:
            name = u'%s (%s)' % (res.folio_id.name, res.room_id.name)
            result.append((res.id, name))
        return result

    @api.multi
    def _computed_shared(self):
        # Has this reservation more charges associates in folio?, Yes?, then, this is share folio ;)
        for record in self:
            if record.folio_id:
                if len(record.folio_id.room_lines) > 1 or \
                        record.folio_id.service_line_ids.filtered(lambda x: (
                        x.ser_room_line != record.id)):
                    record.shared_folio = True
                else:
                    record.shared_folio = False

    @api.depends('checkin', 'checkout')
    def _computed_nights(self):
        for res in self:
            if res.checkin and res.checkout:
                res.nights = (fields.Date.from_string(res.checkout) - fields.Date.from_string(res.checkin)).days

    _name = 'hotel.reservation'
    _description = 'Hotel Reservation'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = "last_updated_res desc, name"

    name = fields.Text('Reservation Description', required=True)

    room_id = fields.Many2one('hotel.room', string='Room')

    reservation_no = fields.Char('Reservation No', size=64, readonly=True)
    adults = fields.Integer('Adults', size=64, readonly=False,
                            track_visibility='onchange',
                            help='List of adults there in guest list. ')
    children = fields.Integer('Children', size=64, readonly=False,
                              track_visibility='onchange',
                              help='Number of children there in guest list.')
    to_assign = fields.Boolean('To Assign', track_visibility='onchange')
    state = fields.Selection([('draft', 'Pre-reservation'), ('confirm', 'Pending Entry'),
                              ('booking', 'On Board'), ('done', 'Out'),
                              ('cancelled', 'Cancelled')],
                             'State', readonly=True,
                             default=lambda *a: 'draft',
                             track_visibility='onchange')
    reservation_type = fields.Selection(related='folio_id.reservation_type',
                                        default=lambda *a: 'normal')
    cancelled_reason = fields.Selection([
        ('late', 'Late'),
        ('intime', 'In time'),
        ('noshow', 'No Show')], 'Cause of cancelled')
    out_service_description = fields.Text('Cause of out of service')

    folio_id = fields.Many2one('hotel.folio', string='Folio',
                               ondelete='cascade')

    checkin = fields.Date('Check In', required=True,
                          default=_get_default_checkin,
                          track_visibility='onchange')
    checkout = fields.Date('Check Out', required=True,
                           default=_get_default_checkout,
                           track_visibility='onchange')
    arrival_hour = fields.Char('Arrival Hour',
                               default=_get_default_arrival_hour,
                               help="Default Arrival Hour (HH:MM)")
    departure_hour = fields.Char('Departure Hour',
                                 default=_get_default_departure_hour,
                                 help="Default Departure Hour (HH:MM)")
    room_type_id = fields.Many2one('hotel.room.type', string='Room Type',
                                   required=True, track_visibility='onchange')

    partner_id = fields.Many2one(related='folio_id.partner_id')
    company_id = fields.Many2one('res.company', 'Company')
    reservation_line_ids = fields.One2many('hotel.reservation.line',
                                           'reservation_id',
                                           readonly=True, required=True,
                                           states={
                                               'draft': [('readonly', False)],
                                               'sent': [('readonly', False)],
                                               'confirm': [('readonly', False)],
                                               'booking': [('readonly', False)],
                                           })
    reserve_color = fields.Char(compute='_compute_color', string='Color',
                                store=True)
    reserve_color_text = fields.Char(compute='_compute_color', string='Color',
                                     store=True)
    service_line_ids = fields.One2many('hotel.service', 'ser_room_line')

    pricelist_id = fields.Many2one('product.pricelist',
                                   related='folio_id.pricelist_id',
                                   readonly="1")
    cardex_ids = fields.One2many('cardex', 'reservation_id')
    # TODO: As cardex_count is a computed field, it can't not be used in a domain filer
    # Non-stored field hotel.reservation.cardex_count cannot be searched
    # searching on a computed field can also be enabled by setting the search parameter.
    # The value is a method name returning a Domains
    cardex_count = fields.Integer('Cardex counter',
                                  compute='_compute_cardex_count')
    cardex_pending = fields.Boolean('Cardex Pending',
                                    compute='_compute_cardex_count',
                                    search='_search_cardex_pending')
    cardex_pending_num = fields.Integer('Cardex Pending Num',
                                        compute='_compute_cardex_count')
    # check_rooms = fields.Boolean('Check Rooms')
    is_checkin = fields.Boolean()
    is_checkout = fields.Boolean()
    splitted = fields.Boolean('Splitted', default=False)
    parent_reservation = fields.Many2one('hotel.reservation',
                                         'Parent Reservation')
    overbooking = fields.Boolean('Is Overbooking', default=False)
    
    nights = fields.Integer('Nights', compute='_computed_nights', store=True)
    channel_type = fields.Selection([
        ('door', 'Door'),
        ('mail', 'Mail'),
        ('phone', 'Phone'),
        ('call', 'Call Center'),
        ('web', 'Web')], 'Sales Channel', default='door')
    last_updated_res = fields.Datetime('Last Updated')
    folio_pending_amount = fields.Monetary(related='folio_id.pending_amount')
    segmentation_ids = fields.Many2many(related='folio_id.segmentation_ids')
    shared_folio = fields.Boolean(compute='_computed_shared')
    #Used to notify is the reservation folio has other reservations or services
    email = fields.Char('E-mail', related='partner_id.email')
    mobile = fields.Char('Mobile', related='partner_id.mobile')
    phone = fields.Char('Phone', related='partner_id.phone')
    partner_internal_comment = fields.Text(string='Internal Partner Notes',
                                           related='partner_id.comment')
    folio_internal_comment = fields.Text(string='Internal Folio Notes',
                                         related='folio_id.internal_comment')
    preconfirm = fields.Boolean('Auto confirm to Save', default=True)
    to_send = fields.Boolean('To Send', default=True)
    has_confirmed_reservations_to_send = fields.Boolean(
                        related='folio_id.has_confirmed_reservations_to_send',
                        readonly=True)
    has_cancelled_reservations_to_send = fields.Boolean(
                        related='folio_id.has_cancelled_reservations_to_send',
                        readonly=True)
    has_checkout_to_send = fields.Boolean(
                        related='folio_id.has_checkout_to_send',
                        readonly=True)
    # order_line = fields.One2many('sale.order.line', 'order_id', string='Order Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)
    # product_id = fields.Many2one('product.product', related='order_line.product_id', string='Product')
    # product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)
    # product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)

    currency_id = fields.Many2one('res.currency',
                                   related='pricelist_id.currency_id',
                                   string='Currency', readonly=True, required=True)
    # invoice_status = fields.Selection([
    #     ('upselling', 'Upselling Opportunity'),
    #     ('invoiced', 'Fully Invoiced'),
    #     ('to invoice', 'To Invoice'),
    #     ('no', 'Nothing to Invoice')
    #     ], string='Invoice Status', compute='_compute_invoice_status', store=True, readonly=True, default='no')
    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    # qty_to_invoice = fields.Float(
    #     string='To Invoice', store=True, readonly=True,
    #     digits=dp.get_precision('Product Unit of Measure'))
    # qty_invoiced = fields.Float(
    #     compute='_get_invoice_qty', string='Invoiced', store=True, readonly=True,
    #     digits=dp.get_precision('Product Unit of Measure'))
    # qty_delivered = fields.Float(string='Delivered', copy=False, digits=dp.get_precision('Product Unit of Measure'), default=0.0)
    # qty_delivered_updateable = fields.Boolean(compute='_compute_qty_delivered_updateable', string='Can Edit Delivered', readonly=True, default=True)
    price_subtotal = fields.Monetary(string='Subtotal', readonly=True, store=True, compute='_compute_amount_reservation')
    price_total = fields.Monetary(string='Total', readonly=True, store=True, compute='_compute_amount_reservation')
    price_tax = fields.Float(string='Taxes', readonly=True, store=True, compute='_compute_amount_reservation')
    # FIXME discount per night
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)

    # analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')

    @api.model
    def create(self, vals):
        vals.update(self._prepare_add_missing_fields(vals))
        if 'folio_id' in vals:
            folio = self.env["hotel.folio"].browse(vals['folio_id'])
            vals.update({'channel_type': folio.channel_type})
        elif 'partner_id' in vals:
            folio_vals = {'partner_id':int(vals.get('partner_id')),
                          'channel_type': vals.get('channel_type')}
            # Create the folio in case of need (To allow to create reservations direct)
            folio = self.env["hotel.folio"].create(folio_vals)
            vals.update({'folio_id': folio.id,
                         'reservation_type': vals.get('reservation_type'),
                         'channel_type': vals.get('channel_type')})
        #~ colors = self._generate_color()
        vals.update({
            'last_updated_res': date_utils.now(hours=True).strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            #~ 'reserve_color': colors[0],
            #~ 'reserve_color_text': colors[1],
        })
        if self.compute_price_out_vals(vals):
            vals.update(self.env['hotel.reservation'].prepare_reservation_lines(vals))
        record = super(HotelReservation, self).create(vals)
        #~ if (record.state == 'draft' and record.folio_id.state == 'sale') or \
                #~ record.preconfirm:
            #~ record.confirm()
        return record

    @api.multi
    def write(self, vals):
        if self.notify_update(vals):
            vals.update({
                'last_updated_res': date_utils.now(hours=True).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            })
        for record in self:
            if record.compute_price_out_vals(vals):
                days_diff = (fields.Date.from_string(record.checkout) - fields.Date.from_string(record.checkin)).days
                record.update(record.prepare_reservation_lines(
                    record.checkin,
                    days_diff,
                    vals = vals)) #REVISAR el unlink
            if ('checkin' in vals and record.checkin != vals['checkin']) or \
                    ('checkout' in vals and record.checkout != vals['checkout']) or \
                    ('state' in vals and record.state != vals['state']) :
                vals.update({'to_send': True})
        res = super(HotelReservation, self).write(vals)
        return res

    @api.model
    def _prepare_add_missing_fields(self, values):
        """ Deduce missing required fields from the onchange """
        res = {}
        onchange_fields = ['room_id', 'pricelist_id',
            'reservation_type', 'currency_id']
        if values.get('partner_id') and values.get('room_type_id') and any(f not in values for f in onchange_fields):
            line = self.new(values)
            line.onchange_room_id()
            for field in onchange_fields:
                if field not in values:
                    res[field] = line._fields[field].convert_to_write(line[field], line)
        return res

    @api.multi
    def notify_update(self, vals):
        if 'checkin' in vals or \
                'checkout' in vals or \
                'discount' in vals or \
                'state' in vals or \
                'room_type_id' in vals or \
                'to_assign' in vals:
            return  True
        return False
        
    @api.multi
    def overbooking_button(self):
        self.ensure_one()
        return self.write({'overbooking': not self.overbooking})

    @api.multi
    def open_folio(self):
        action = self.env.ref('hotel.open_hotel_folio1_form_tree_all').read()[0]
        if self.folio_id:
            action['views'] = [(self.env.ref('hotel.view_hotel_folio1_form').id, 'form')]
            action['res_id'] = self.folio_id.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def open_reservation_form(self):
        action = self.env.ref('hotel.open_hotel_reservation_form_tree_all').read()[0]
        action['views'] = [(self.env.ref('hotel.view_hotel_reservation_form').id, 'form')]
        action['res_id'] = self.id
        return action

    @api.multi
    def generate_copy_values(self, checkin=False, checkout=False):
        self.ensure_one()
        return {
            'name': self.name,
            'adults': self.adults,
            'children': self.children,
            'checkin': checkin or self.checkin,
            'checkout': checkout or self.checkout,
            'folio_id': self.folio_id.id,
            # 'product_id': self.product_id.id,
            'parent_reservation': self.parent_reservation.id,
            'state': self.state,
            'overbooking': self.overbooking,
            'price_unit': self.price_unit,
            'splitted': self.splitted,
            # 'virtual_room_id': self.virtual_room_id.id,
            'room_type_id': self.room_type_id.id,
        }

    @api.constrains('adults')
    def _check_adults(self):
        for record in self:
            if record.adults > record.room_id.capacity:
                    raise ValidationError(
                        _("Reservation persons can't be higher than room capacity"))
            if record.adults == 0:
                raise ValidationError(_("Reservation has no adults"))

    """
    ONCHANGES ----------------------------------------------------------
    """

    @api.onchange('adults', 'room_id')
    def onchange_room_id(self):
        # TODO: Usar vals y write
        if self.room_id:
            if self.room_id.capacity < self.adults:
                self.adults = self.room_id.capacity
                raise UserError(
                    _('%s people do not fit in this room! ;)') % (persons))
            if self.adults == 0:
                self.adults = self.room_id.capacity
            if not self.room_type_id: #Si el registro no existe, modificar room_type aunque ya esté establecido
                self.room_type_id = self.room_id.room_type_id

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        #TODO: Change parity pricelist by default pricelist
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or \
                self.env['ir.default'].sudo().get('hotel.config.settings', 'parity_pricelist_id'),
        }
        self.update(values)

    # When we need to overwrite the prices even if they were already established
    @api.onchange('room_type_id', 'pricelist_id', 'reservation_type')
    def onchange_overwrite_price_by_day(self):
        if self.room_type_id and self.checkin and self.checkout:
            days_diff = (fields.Date.from_string(self.checkout) - fields.Date.from_string(self.checkin)).days
            self.update(self.prepare_reservation_lines(
                self.checkin,
                days_diff,
                update_old_prices = True))

    # When we need to update prices respecting those that were already established
    @api.onchange('checkin', 'checkout')
    def onchange_dates(self):
        if not self.checkin:
            self.checkin = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if not self.checkout:
            self.checkout = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        checkin_dt = fields.Date.from_string(self.checkin)
        checkout_dt = fields.Date.from_string(self.checkout)
        if checkin_dt >= checkout_dt:
            self.checkout = (fields.Date.from_string(self.checkin) + timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
        if self.room_type_id:
            days_diff = (fields.Date.from_string(self.checkout) - fields.Date.from_string(self.checkin)).days
            self.update(self.prepare_reservation_lines(
                self.checkin,
                days_diff,
                update_old_prices = False))
        
        

    @api.onchange('checkin', 'checkout', 'room_type_id')
    def onchange_compute_reservation_description(self):
        if self.room_type_id and self.checkin and self.checkout:
            checkin_dt = fields.Date.from_string(self.checkin)
            checkout_dt = fields.Date.from_string(self.checkout)
            checkin_str = checkin_dt.strftime('%d/%m/%Y')
            checkout_str = checkout_dt.strftime('%d/%m/%Y')
            self.name = self.room_type_id.name + ': ' + checkin_str + ' - '\
                + checkout_str

    @api.multi
    @api.onchange('checkin', 'checkout', 'room_id')
    def onchange_room_availabiltiy_domain(self):
        self.ensure_one()
        if self.checkin and self.checkout:
            if self.overbooking:
                return
            occupied = self.env['hotel.reservation'].get_reservations(
                self.checkin,
                fields.Date.from_string(self.checkout).strftime(DEFAULT_SERVER_DATE_FORMAT)).filtered(
                    lambda r: r.id != self._origin.id)
            rooms_occupied = occupied.mapped('room_id.id')
            if self.room_id and self.room_id.id in rooms_occupied:
                warning_msg = _('You tried to change \
                       reservation with room those already reserved in this \
                       reservation period')
                raise ValidationError(warning_msg)
            domain_rooms = [
                ('id', 'not in', rooms_occupied)
            ]
            return {'domain': {'room_id': domain_rooms}}

    """
    COMPUTE RESERVE COLOR ----------------------------------------------
    """

    @api.multi
    def _generate_color(self):
        self.ensure_one()
        now_utc_dt = date_utils.now()
        # unused variables
        # diff_checkin_now = date_utils.date_diff(now_utc_dt, self.checkin,
        #                                         hours=False)
        # diff_checkout_now = date_utils.date_diff(now_utc_dt, self.checkout,
        #                                          hours=False)

        ir_values_obj = self.env['ir.default']
        reserv_color = '#FFFFFF'
        reserv_color_text = '#000000'
        # FIXME added for migration
        return ('#4E9DC4', '#000000')

        if self.reservation_type == 'staff':
            reserv_color = ir_values_obj.get('res.config.settings',
                                                     'color_staff')
            reserv_color_text = ir_values_obj.get(
                'res.config.settings',
                'color_letter_staff')
        elif self.reservation_type == 'out':
            reserv_color = ir_values_obj.get('res.config.settings',
                                                     'color_dontsell')
            reserv_color_text = ir_values_obj.get(
                'res.config.settings',
                'color_letter_dontsell')
        elif self.to_assign:
            reserv_color = ir_values_obj.get('res.config.settings',
                                                     'color_to_assign')
            reserv_color_text = ir_values_obj.get(
                'res.config.settings',
                'color_letter_to_assign')
        elif self.state == 'draft':
            reserv_color = ir_values_obj.get('res.config.settings',
                                                     'color_pre_reservation')
            reserv_color_text = ir_values_obj.get(
                'res.config.settings',
                'color_letter_pre_reservation')
        elif self.state == 'confirm':
            if self.folio_id.pending_amount == 0:
                reserv_color = ir_values_obj.get(
                    'res.config.settings', 'color_reservation_pay')
                reserv_color_text = ir_values_obj.get(
                    'res.config.settings', 'color_letter_reservation_pay')
            else:
                reserv_color = ir_values_obj.get(
                    'res.config.settings', 'color_reservation')
                reserv_color_text = ir_values_obj.get(
                    'res.config.settings', 'color_letter_reservation')
        elif self.state == 'booking':
            if self.folio_id.pending_amount == 0:
                reserv_color = ir_values_obj.get(
                    'res.config.settings', 'color_stay_pay')
                reserv_color_text = ir_values_obj.get(
                    'res.config.settings', 'color_letter_stay_pay')
            else:
                reserv_color = ir_values_obj.get(
                    'res.config.settings', 'color_stay')
                reserv_color_text = ir_values_obj.get(
                    'res.config.settings', 'color_letter_stay')
        else:
            if self.folio_id.pending_amount == 0:
                reserv_color = ir_values_obj.get(
                    'res.config.settings', 'color_checkout')
                reserv_color_text = ir_values_obj.get(
                    'res.config.settings', 'color_letter_checkout')
            else:
                reserv_color = ir_values_obj.get(
                    'res.config.settings', 'color_payment_pending')
                reserv_color_text = ir_values_obj.get(
                    'res.config.settings', 'color_letter_payment_pending')
        return (reserv_color, reserv_color_text)

    @api.depends('state', 'reservation_type', 'folio_id.pending_amount', 'to_assign')
    def _compute_color(self):
        _logger.info('_compute_color')
        for rec in self:
            colors = rec._generate_color()
            rec.update({
                'reserve_color': colors[0],
                'reserve_color_text': colors[1],
            })
            rec.folio_id.color = colors[0]

            # hotel_reserv_obj = self.env['hotel.reservation']
            # if rec.splitted:
            #     master_reservation = rec.parent_reservation or rec
            #     splitted_reservs = hotel_reserv_obj.search([
            #         ('splitted', '=', True),
            #         '|', ('parent_reservation', '=', master_reservation.id),
            #              ('id', '=', master_reservation.id),
            #         ('folio_id', '=', rec.folio_id.id),
            #         ('id', '!=', rec.id),
            #     ])
            #     splitted_reservs.write({'reserve_color': rec.reserve_color})

    """
    STATE WORKFLOW -----------------------------------------------------
    """

    @api.multi
    def confirm(self):
        '''
        @param self: object pointer
        '''
        _logger.info('confirm')
        hotel_folio_obj = self.env['hotel.folio']
        hotel_reserv_obj = self.env['hotel.reservation']
        for r in self:
            vals = {}
            if r.cardex_ids:
                vals.update({'state': 'booking'})
            else:
                vals.update({'state': 'confirm'})
            if r.checkin_is_today():
                vals.update({'is_checkin': True})
                folio = hotel_folio_obj.browse(r.folio_id.id)
                folio.checkins_reservations = folio.room_lines.search_count([
                    ('folio_id', '=', folio.id), ('is_checkin', '=', True)])
            r.write(vals)

            if r.splitted:
                master_reservation = r.parent_reservation or r
                splitted_reservs = hotel_reserv_obj.search([
                    ('splitted', '=', True),
                    '|', ('parent_reservation', '=', master_reservation.id),
                         ('id', '=', master_reservation.id),
                    ('folio_id', '=', r.folio_id.id),
                    ('id', '!=', r.id),
                    ('state', '!=', 'confirm')
                ])
                splitted_reservs.confirm()
        return True

    @api.multi
    def button_done(self):
        '''
        @param self: object pointer
        '''
        for res in self:
            res.action_reservation_checkout()
        return True

    @api.multi
    def action_cancel(self):
        for record in self:
            record.write({
                'state': 'cancelled',
                'discount': 100.0,
            })
            if record.checkin_is_today:
                record.is_checkin = False
                folio = self.env['hotel.folio'].browse(record.folio_id.id)
                folio.checkins_reservations = folio.room_lines.search_count([
                    ('folio_id', '=', folio.id),
                    ('is_checkin', '=', True)
                ])

            if record.splitted:
                master_reservation = record.parent_reservation or record
                splitted_reservs = self.env['hotel.reservation'].search([
                    ('splitted', '=', True),
                    '|', ('parent_reservation', '=', master_reservation.id),
                         ('id', '=', master_reservation.id),
                    ('folio_id', '=', record.folio_id.id),
                    ('id', '!=', record.id),
                    ('state', '!=', 'cancelled')
                ])
                splitted_reservs.action_cancel()
            record.folio_id.compute_amount()

    @api.multi
    def draft(self):
        for record in self:
            record.write({'state': 'draft'})

            if record.splitted:
                master_reservation = record.parent_reservation or record
                splitted_reservs = self.env['hotel.reservation'].search([
                    ('splitted', '=', True),
                    '|', ('parent_reservation', '=', master_reservation.id),
                         ('id', '=', master_reservation.id),
                    ('folio_id', '=', record.folio_id.id),
                    ('id', '!=', record.id),
                    ('state', '!=', 'draft')
                ])
                splitted_reservs.draft()

    """
    PRICE PROCESS ------------------------------------------------------
    """
    @api.multi
    def compute_price_out_vals(self, vals):
        """
        Compute if It is necesary calc price in write/create
        """
        if not vals:
            vals = {}
        if ('reservation_line_ids' not in vals and \
                ('checkout' in vals or 'checkin' in vals or \
                'room_type_id' in vals or 'pricelist_id' in vals)):
            return True
        return False
    
    @api.depends('reservation_line_ids', 'reservation_line_ids.discount', 'tax_id')
    def _compute_amount_reservation(self):
        """
        Compute the amounts of the reservation.
        """
        for line in self:
            amount_room = 0
            for day in line.reservation_line_ids:
                 amount_room += day.price
            if amount_room > 0:
                product = line.room_type_id.product_id
                price = amount_room * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_id.compute_all(price, line.currency_id, 1, product=product)
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })

    @api.multi
    def prepare_reservation_lines(self, dfrom, days, vals=False,
                                  update_old_prices=False):
        total_price = 0.0
        cmds = []
        if not vals:
            vals = {}
        pricelist_id = self.env['ir.default'].sudo().get(
            'res.config.settings', 'parity_pricelist_id')
        #~ pricelist_id = vals.get('pricelist_id') or self.pricelist_id.id
        product = self.env['hotel.room.type'].browse(vals.get('room_type_id') or self.room_type_id.id).product_id
        old_lines_days = self.mapped('reservation_line_ids.date')
        partner = self.env['res.partner'].browse(vals.get('partner_id') or self.partner_id.id)
        total_price = 0
        for i in range(0, days):
            idate = (fields.Date.from_string(dfrom) + timedelta(days=i)).strftime(DEFAULT_SERVER_DATE_FORMAT)
            old_line = self.reservation_line_ids.filtered(lambda r: r.date == idate)
            if update_old_prices or (idate not in old_lines_days):                
                product = product.with_context(
                     lang=partner.lang,
                     partner=partner.id,
                     quantity=1,
                     date=idate,
                     pricelist=pricelist_id,
                     uom=product.uom_id.id)
                line_price = self.env['account.tax']._fix_tax_included_price_company(product.price, product.taxes_id, self.tax_id, self.company_id)
                if old_line:
                    cmds.append((1, old_line.id, {
                        'price': line_price
                    }))
                else:
                    cmds.append((0, False, {
                        'date': idate,
                        'price': line_price
                    }))
            else:
                line_price = old_line.price
                cmds.append((4, old_line.id))
            total_price += line_price
        return {'reservation_line_ids': cmds}

    @api.multi
    def action_pay_folio(self):
        self.ensure_one()
        return self.folio_id.action_pay()

    @api.multi
    def action_pay_reservation(self):
        self.ensure_one()
        partner = self.partner_id.id
        amount = min(self.amount_reservation, self.folio_pending_amount)
        note = self.folio_id.name + ' (' + self.name + ')'
        view_id = self.env.ref('hotel.view_account_payment_folio_form').id
        return{
            'name': _('Register Payment'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'context': {
                'default_folio_id': self.folio_id.id,
                'default_room_id': self.id,
                'default_amount': amount,
                'default_payment_type': 'inbound',
                'default_partner_type': 'customer',
                'default_partner_id': partner,
                'default_communication': note,
            },
            'target': 'new',
        }

    """
    AVAILABILTY PROCESS ------------------------------------------------
    """

    @api.model
    def get_reservations(self, dfrom, dto):
        """
        @param self: The object pointer
        @param dfrom: range date from
        @param dto: range date to
        @return: array with the reservations _confirmed_ between dfrom and dto
        """
        domain = [('reservation_line_ids.date', '>=', dfrom),
                  ('reservation_line_ids.date', '<', dto),
                  ('state', '!=', 'cancelled'),
                  ('overbooking', '=', False)]
        reservations = self.env['hotel.reservation'].search(domain)
        return self.env['hotel.reservation'].search(domain)

    @api.model
    def get_reservations_dates(self, dfrom, dto, room_type=False):
        """
        @param self: The object pointer
        @param dfrom: range date from
        @param dto: range date to
        @return: dictionary of lists with reservations (a hash of arrays!)
                 with the reservations dates between dfrom and dto
        reservations_dates
            {'2018-07-30': [hotel.reservation(29,), hotel.reservation(30,),
                           hotel.reservation(31,)],                           
             '2018-07-31': [hotel.reservation(22,), hotel.reservation(35,),
                           hotel.reservation(36,)],
            }
        """
        domain = [('date', '>=', dfrom),
                  ('date', '<', dto)]
        lines = self.env['hotel.reservation.line'].search(domain)
        reservations_dates = {}
        for record in lines:
            # kumari.net/index.php/programming/programmingcat/22-python-making-a-dictionary-of-lists-a-hash-of-arrays
            # reservations_dates.setdefault(record.date,[]).append(record.reservation_id.room_type_id)
            reservations_dates.setdefault(record.date, []).append(
                [record.reservation_id, record.reservation_id.room_type_id])
        return reservations_dates

    # TODO: Use default values on checkin /checkout is empty
    @api.constrains('checkin', 'checkout', 'state', 'room_id', 'overbooking')
    def check_dates(self):
        """
        1.-When date_order is less then checkin date or
        Checkout date should be greater than the checkin date.
        3.-Check the reservation dates are not occuped
        """
        _logger.info('check_dates')
        if fields.Date.from_string(self.checkin) >= fields.Date.from_string(self.checkout):
            raise ValidationError(_('Room line Check In Date Should be \
                less than the Check Out Date!'))
        if not self.overbooking and not self._context.get("ignore_avail_restrictions", False):
            occupied = self.env['hotel.reservation'].get_reservations(
                self.checkin,
                self.checkout)
            occupied = occupied.filtered(
                lambda r: r.room_id.id == self.room_id.id
                and r.id != self.id)
            occupied_name = ','.join(str(x.room_id.name) for x in occupied)
            if occupied:
                warning_msg = _('You tried to change/confirm \
                   reservation with room those already reserved in this \
                   reservation period: %s ') % occupied_name
                raise ValidationError(warning_msg)

    """
    CHECKIN/OUT PROCESS ------------------------------------------------
    """

    @api.multi
    def _compute_cardex_count(self):
        _logger.info('_compute_cardex_count')
        for res in self:
            res.cardex_count = len(res.cardex_ids)
            res.cardex_pending_num = (res.adults + res.children) \
                - len(res.cardex_ids)
            if (res.adults + res.children - len(res.cardex_ids)) <= 0:
                res.cardex_pending = False
            else:
                res.cardex_pending = True

    # https://www.odoo.com/es_ES/forum/ayuda-1/question/calculated-fields-in-search-filter-possible-118501
    @api.multi
    def _search_cardex_pending(self, operator, value):
        recs = self.search([]).filtered(lambda x: x.cardex_pending is True)
        if recs:
            return [('id', 'in', [x.id for x in recs])]
    
    @api.multi
    def action_reservation_checkout(self):
        for record in self:
            record.state = 'done'
            if record.checkout_is_today():
                record.is_checkout = False
                folio = self.env['hotel.folio'].browse(self.folio_id.id)
                folio.checkouts_reservations = folio.room_lines.search_count([
                    ('folio_id', '=', folio.id),
                    ('is_checkout', '=', True)
                ])

    @api.model
    def daily_plan(self):
        _logger.info('daily_plan')
        today_utc_dt = date_utils.now()
        yesterday_utc_dt = today_utc_dt - timedelta(days=1)
        hotel_tz = self.env['ir.default'].sudo().get('res.config.settings',
                                                     'tz_hotel')
        today_dt = date_utils.dt_as_timezone(today_utc_dt, hotel_tz)
        yesterday_dt = date_utils.dt_as_timezone(yesterday_utc_dt, hotel_tz)

        today_str = today_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        yesterday_str = yesterday_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        reservations_to_checkout = self.env['hotel.reservation'].search([
            ('state', 'not in', ['done']),
            ('checkout', '<', today_str)
            ])
        for res in reservations_to_checkout:
            res.action_reservation_checkout()

        reservations = self.env['hotel.reservation'].search([
            ('reservation_line_ids.date', 'in', [today_str,
                                              yesterday_str]),
            ('state', 'in', ['confirm', 'booking'])
        ])
        self._cr.execute("update hotel_reservation set is_checkin = False, \
                            is_checkout = False where is_checkin = True or \
                            is_checkout = True")
        checkins_res = reservations.filtered(lambda x: (
            x.state in ('confirm','draft')
            and date_utils.date_compare(x.checkin, today_str, hours=False)
            and x.reservation_type == 'normal'))
        checkins_res.write({'is_checkin': True})
        checkouts_res = reservations.filtered(lambda x: (
            x.state not in ('done','cancelled')
            and date_utils.date_compare(x.checkout, today_str,
                                        hours=False)
            and x.reservation_type == 'normal'))
        checkouts_res.write({'is_checkout': True})
        self.env['hotel.folio'].daily_plan()
        return True

    @api.model
    def checkin_is_today(self):
        self.ensure_one()
        tz_hotel = self.env['ir.default'].sudo().get(
            'res.config.settings', 'tz_hotel')
        today = fields.Date.context_today(self.with_context(tz=tz_hotel))
        return self.checkin == today

    @api.model
    def checkout_is_today(self):
        self.ensure_one()
        tz_hotel = self.env['ir.default'].sudo().get(
            'res.config.settings', 'tz_hotel')
        today = fields.Date.context_today(self.with_context(tz=tz_hotel))
        return self.checkout == today

    @api.multi
    def action_checks(self):
        self.ensure_one()
        return {
            'name': _('Cardexs'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'cardex',
            'type': 'ir.actions.act_window',
            'domain': [('reservation_id', '=', self.id)],
            'target': 'new',
        }

    """
    RESERVATION SPLITTED -----------------------------------------------
    """

    @api.multi
    def get_real_checkin_checkout(self):
        self.ensure_one()
        if not self.splitted:
            return (self.checkin, self.checkout)

        master_reservation = self.parent_reservation or self
        splitted_reservs = self.env['hotel.reservation'].search([
            ('splitted', '=', True),
            ('folio_id', '=', self.folio_id.id),
            '|',
            ('parent_reservation', '=', master_reservation.id),
            ('id', '=', master_reservation.id)
        ])
        last_checkout = splitted_reservs[0].checkout
        first_checkin = splitted_reservs[0].checkin
        for reserv in splitted_reservs:
            if last_checkout < reserv.checkout:
                last_checkout = reserv.checkout
            if first_checkin > reserv.checkin:
                first_checkin = reserv.checkin
        return (first_checkin, last_checkout)

    @api.multi
    def unify(self):
        # FIXME Remove product inheritance
        pass
    #     self.ensure_one()
    #     if not self.splitted:
    #         raise ValidationError(_("This reservation can't be unified"))
    #
    #     master_reservation = self.parent_reservation or self
    #     self_is_master = (master_reservation == self)
    #
    #     splitted_reservs = self.env['hotel.reservation'].search([
    #         ('splitted', '=', True),
    #         ('folio_id', '=', self.folio_id.id),
    #         '|',
    #         ('parent_reservation', '=', master_reservation.id),
    #         ('id', '=', master_reservation.id)
    #     ])
    #
    #     rooms_products = splitted_reservs.mapped('product_id.id')
    #     if len(rooms_products) > 1 or \
    #             (len(rooms_products) == 1
    #                 and master_reservation.product_id.id != rooms_products[0]):
    #         raise ValidationError(_("This reservation can't be unified: They \
    #                                 all need to be in the same room"))
    #
    #     # Search checkout
    #     last_checkout = splitted_reservs[0].checkout
    #     for reserv in splitted_reservs:
    #         if last_checkout < reserv.checkout:
    #             last_checkout = reserv.checkout
    #
    #     # Agrupate reservation lines
    #     reservation_line_ids = splitted_reservs.mapped('reservation_line_ids')
    #     reservation_line_ids.sorted(key=lambda r: r.date)
    #     rlines = [(5, False, False)]
    #     tprice = 0.0
    #     for rline in reservation_line_ids:
    #         rlines.append((0, False, {
    #             'date': rline.date,
    #             'price': rline.price,
    #         }))
    #         tprice += rline.price
    #
    #     # Unify
    #     folio = self.folio_id   # FIX: To Allow Unify confirm reservations
    #     state = folio.state     # FIX
    #     folio.state = 'draft'   # FIX
    #     osplitted_reservs = splitted_reservs - master_reservation
    #     osplitted_reservs.sudo().unlink()
    #     folio.state = state  # FIX
    #
    #     # FIXME: Two writes because checkout regenerate reservation lines
    #     master_reservation.write({
    #         'checkout': last_checkout,
    #         'splitted': False,
    #     })
    #     master_reservation.write({
    #         'reservation_line_ids': rlines,
    #         'price_unit': tprice,
    #     })
    #     if not self_is_master:
    #         return {'type': 'ir.actions.act_window_close'}
    #     return True
    #
    # '''
    #       Created this because "copy()" function create a new record
    #     and collide with date restrictions.
    #     This function generate a usable dictionary with reservation values
    #     for copy purposes.
    # '''

    @api.multi
    def open_master(self):
        self.ensure_one()
        if not self.parent_reservation:
            raise ValidationError(_("This is the parent reservation"))
        action = self.env.ref('hotel.open_hotel_reservation_form_tree_all').read()[0]
        action['views'] = [(self.env.ref('hotel.view_hotel_reservation_form').id, 'form')]
        action['res_id'] = self.parent_reservation.id
        return action

    """
    MAILING PROCESS
    """

    @api.multi
    def send_reservation_mail(self):
        return self.folio_id.send_reservation_mail()

    @api.multi
    def send_exit_mail(self):
        return self.folio_id.send_exit_mail()

    @api.multi
    def send_cancel_mail(self):
        return self.folio_id.send_cancel_mail()

