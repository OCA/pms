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
from datetime import datetime, timedelta, date
from odoo.addons.hotel import date_utils
import pytz
import time
import logging
_logger = logging.getLogger(__name__)

from odoo.addons import decimal_precision as dp

class HotelReservation(models.Model):

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
            if self.folio_id.invoices_amount == 0:
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
            if self.folio_id.invoices_amount == 0:
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
            if self.folio_id.invoices_amount == 0:
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

    @api.depends('state', 'reservation_type', 'folio_id.invoices_amount', 'to_assign')
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

    @api.multi
    def copy(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''

        return super(HotelReservation, self).copy(default=default)

    @api.multi
    def _amount_line(self, field_name, arg):
        '''
        @param self: object pointer
        @param field_name: Names of fields.
        @param arg: User defined arguments
        '''
        return False
        # return self.env['sale.order.line']._amount_line(field_name, arg)

    @api.multi
    def _number_packages(self, field_name, arg):
        '''
        @param self: object pointer
        @param field_name: Names of fields.
        @param arg: User defined arguments
        '''
        return False
        # return self.env['sale.order.line']._number_packages(field_name, arg)

    @api.multi
    def set_call_center_user(self):
        user = self.env['res.users'].browse(self.env.uid)
        rec.call_center = user.has_group('hotel.group_hotel_call')

    @api.multi
    def _get_default_checkin(self):
        folio = False
        # default_arrival_hour = self.env['ir.default'].sudo().get(
        #     'res.config.settings', 'default_arrival_hour')
        if 'folio_id' in self._context:
            folio = self.env['hotel.folio'].search([
                ('id', '=', self._context['folio_id'])
            ])
        if folio and folio.room_lines:
            return folio.room_lines[0].checkin
        else:
            # tz_hotel = self.env['ir.default'].sudo().get(
            #     'res.config.settings', 'tz_hotel')
            # now_utc_dt = date_utils.now()
            # ndate = "%s %s:00" % \
            #     (now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            #      default_arrival_hour)
            # ndate_dt = date_utils.get_datetime(ndate, stz=tz_hotel)
            # ndate_dt = date_utils.dt_as_timezone(ndate_dt, 'UTC')
            # return ndate_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            # return fields.Date.today() ¿?
            return fields.Date.context_today(self)

    @api.multi
    def _get_default_checkout(self):
        folio = False
        # default_departure_hour = self.env['ir.default'].sudo().get(
        #     'res.config.settings', 'default_departure_hour')
        if 'folio_id' in self._context:
            folio = self.env['hotel.folio'].search([
                ('id', '=', self._context['folio_id'])
            ])
        if folio and folio.room_lines:
            return folio.room_lines[0].checkout
        else:
            # tz_hotel = self.env['ir.default'].sudo().get(
            #     'res.config.settings', 'tz_hotel')
            # now_utc_dt = date_utils.now() + timedelta(days=1)
            # ndate = "%s %s:00" % \
            #     (now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            #      default_departure_hour)
            # ndate_dt = date_utils.get_datetime(ndate, stz=tz_hotel)
            # ndate_dt = date_utils.dt_as_timezone(ndate_dt, 'UTC')
            # return ndate_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            # return fields.Date.today() ¿?
            return fields.Date.context_today(self, datetime.now() + timedelta(days=1))

    @api.multi
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

    @api.multi
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

    # @api.constrains('checkin', 'checkout') #Why dont run api.depends?¿?
    # def _computed_nights(self):
    #     for res in self:
    #         if res.checkin and res.checkout:
    #             nights = days_diff = date_utils.date_diff(
    #                 self.checkin,
    #                 self.checkout, hours=False)
    #         res.nights = nights

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        if not(name == '' and operator == 'ilike'):
            args += [
                '|',
                ('folio_id.name', operator, name)
                # FIXME Remove product inheritance
                # ('product_id.name', operator, name)
            ]
        return super(HotelReservation, self).name_search(
            name='', args=args, operator='ilike', limit=limit)

    @api.multi
    def name_get(self):
        # FIXME Remove product inheritance
        result = []
        for res in self:
            name = u'%s (%s)' % (res.folio_id.name, res.room_id.name)
            result.append((res.id, name))
        return result

    # FIXME added for migration
    def _compute_qty_delivered_updateable(self):
        pass
    # FIXME added for migration
    def _compute_invoice_status(self):
        pass

    _name = 'hotel.reservation'
    _description = 'Hotel Reservation'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = "last_updated_res desc, name"

    # The record's name should now be used for description of the reservation ?
    name = fields.Text('Reservation Description', required=True)

    # _defaults = {
    #     'product_id': False
    # }

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

    # pricelist_id = fields.Many2one('product.pricelist',
    #                                related='folio_id.pricelist_id',
    #                                readonly="1")
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
    # To show de total amount line in read_only mode
    amount_reservation = fields.Float('Total',
                                      compute='_computed_amount_reservation',
                                      store=True)
    amount_reservation_services = fields.Float('Services Amount',
                                               compute='_computed_amount_reservation',
                                               store=True)
    amount_room = fields.Float('Amount Room', compute="_computed_amount_reservation",
                               store=True)
    amount_discount = fields.Float('Room with Discount', compute="_computed_amount_reservation",
                                   store=True)
    discount_type = fields.Selection([
        ('percent', 'Percent'),
        ('fixed', 'Fixed')], 'Discount Type', default=lambda *a: 'percent')
    discount_fixed = fields.Float('Fixed Discount')

    nights = fields.Integer('Nights', compute='_computed_nights', store=True)
    channel_type = fields.Selection([
        ('door', 'Door'),
        ('mail', 'Mail'),
        ('phone', 'Phone'),
        ('call', 'Call Center'),
        ('web', 'Web')], 'Sales Channel', default='door')
    last_updated_res = fields.Datetime('Last Updated')
    # Monetary to Float
    folio_pending_amount = fields.Float(related='folio_id.invoices_amount')
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
    call_center = fields.Boolean(compute='set_call_center_user')
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
    # fix_total = fields.Boolean(compute='_compute_fix_total')
    # fix_folio_pending = fields.Boolean(related='folio_id.fix_price')

    # order_line = fields.One2many('sale.order.line', 'order_id', string='Order Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)
    # product_id = fields.Many2one('product.product', related='order_line.product_id', string='Product')
    # product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)
    # product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)

    # currency_id = fields.Many2one('res.currency',
    #                               related='pricelist_id.currency_id',
    #                               string='Currency', readonly=True, required=True)
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
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    # Monetary to Float
    price_subtotal = fields.Float(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    # Monetary to Float
    price_total = fields.Float(compute='_compute_amount', string='Total', readonly=True, store=True)

    # FIXME discount per night
    # discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)

    # analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')


    def action_recalcule_payment(self):
        for record in self:
            for res in record.folio_id.room_lines:
                res.on_change_checkin_checkout_product_id()

    def _computed_folio_name(self):
        for res in self:
            res.folio_name = res.folio_id.name + '-' + \
                res.folio_id.date_order

    @api.multi
    def send_reservation_mail(self):
        return self.folio_id.send_reservation_mail()

    @api.multi
    def send_exit_mail(self):
        return self.folio_id.send_exit_mail()

    @api.multi
    def send_cancel_mail(self):
        return self.folio_id.send_cancel_mail()

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

    @api.multi
    def _computed_shared(self):
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
                nights = days_diff = date_utils.date_diff(
                    res.checkin,
                    res.checkout, hours=False)
                res.nights = nights

    @api.model
    def recompute_reservation_totals(self):
        reservations = self.env['hotel.reservation'].search([])
        for res in reservations:
            if res.folio_id.state not in ('done','cancel'):
                _logger.info('---------BOOK-----------')
                _logger.info(res.amount_reservation)
                _logger.info(res.id)
                res._computed_amount_reservation()
                _logger.info(res.amount_reservation)
                _logger.info('---------------------------')

    @api.depends('reservation_line_ids.price')
    def _computed_amount_reservation(self):
        _logger.info('_computed_amount_reservation')
        # FIXME commented during migration
        # import wdb; wdb.set_trace()
        # for res in self:
        #     amount_service = amount_room = 0
        #     for line in res.reservation_line_ids:
        #         amount_room += line.price
        #     for service in res.service_line_ids:
        #         # We must calc the line to can show the price in edit mode
        #         # on smartbutton whithout having to wait to save.
        #         total_line = service.price_unit * service.product_uom_qty
        #         discount = (service.discount * total_line) / 100
        #         amount_service += total_line - discount
        #     res.amount_room = amount_room #To view price_unit with read_only
        #     if res.discount_type == 'fixed' and amount_room > 0:
        #         res.discount = (res.discount_fixed * 100) / amount_room # WARNING Posible division by zero
        #     else:
        #         res.discount_fixed = (res.discount * amount_room) / 100
        #     res.amount_discount = amount_room - res.discount_fixed
        #     res.price_unit = amount_room
        #     res.amount_reservation_services = amount_service
        #     res.amount_reservation = res.amount_discount + amount_service #To the smartbutton

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
        date_now_str = date_utils.now().strftime(
            DEFAULT_SERVER_DATE_FORMAT)
        return date_utils.date_compare(self.checkin, date_now_str, hours=False)

    @api.model
    def checkout_is_today(self):
        self.ensure_one()
        date_now_str = date_utils.now().strftime(
            DEFAULT_SERVER_DATE_FORMAT)
        return date_utils.date_compare(self.checkout, date_now_str,
                                       hours=False)

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
            record.folio_id.compute_invoices_amount()

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

    @api.multi
    def overbooking_button(self):
        self.ensure_one()
        return self.write({'overbooking': not self.overbooking})

    @api.multi
    def open_master(self):
        self.ensure_one()
        if not self.parent_reservation:
            raise ValidationError(_("This is the parent reservation"))
        action = self.env.ref('hotel.open_hotel_reservation_form_tree_all').read()[0]
        action['views'] = [(self.env.ref('hotel.view_hotel_reservation_form').id, 'form')]
        action['res_id'] = self.parent_reservation.id
        return action

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

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for hotel folio line.
        """
        # import wdb; wdb.set_trace()
        if not 'reservation_type' in vals or not vals.get('reservation_type'):
            vals.update({'reservation_type': 'normal'})
        if 'folio_id' in vals:
            folio = self.env["hotel.folio"].browse(vals['folio_id'])
            # vals.update({'order_id': folio.order_id.id,
            #              'channel_type': folio.channel_type})
            vals.update({'channel_type': folio.channel_type})
        elif 'partner_id' in vals:
            folio_vals = {'partner_id':int(vals.get('partner_id')),
                          'channel_type': vals.get('channel_type')}
            folio = self.env["hotel.folio"].create(folio_vals)
            # vals.update({'order_id': folio.order_id.id,
            #              'folio_id': folio.id,
            #              'reservation_type': vals.get('reservation_type'),
            #              'channel_type': vals.get('channel_type')})
            vals.update({'folio_id': folio.id,
                         'reservation_type': vals.get('reservation_type'),
                         'channel_type': vals.get('channel_type')})
        user = self.env['res.users'].browse(self.env.uid)
        if user.has_group('hotel.group_hotel_call'):
            vals.update({'to_assign': True,
                         'channel_type': 'call'})
        vals.update({
            'last_updated_res': date_utils.now(hours=True).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        })
        if folio:
            record = super(HotelReservation, self).create(vals)
            # Check Capacity
            # NOTE the room is not a product anymore
            # room = self.env['hotel.room'].search([
            #     ('product_id', '=', record.product_id.id)
            # ])
            #persons = record.adults     # Not count childrens
            if record.adults > record.room_id.capacity:
                raise ValidationError(
                    _("Reservation persons can't be higher than room capacity"))
            if record.adults == 0:
                raise ValidationError(_("Reservation has no adults"))
            if (record.state == 'draft' and record.folio_id.state == 'sale') or \
                    record.preconfirm:
                record.confirm()
            record._compute_color()
            return record

    @api.multi
    def write(self, vals):
        for record in self:
            if ('checkin' in vals and record.checkin != vals['checkin']) or \
                    ('checkout' in vals and record.checkout != vals['checkout']) or \
                    ('state' in vals and record.state != vals['state']) or \
                    ('amount_discount' in vals and record.amount_discount != vals['amount_discount']):
                vals.update({'to_send': True})

        pricesChanged = ('checkin' in vals or \
                         'checkout' in vals or \
                         'discount' in vals)
        # vals.update({
        #     'edit_room': False,
        # })
        # if pricesChanged or 'state' in vals or 'virtual_room_id' in vals or 'to_assign' in vals:
        if pricesChanged or 'state' in vals or 'room_type_id' in vals or 'to_assign' in vals:
            vals.update({
                'last_updated_res': date_utils.now(hours=True).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            })
            user = self.env['res.users'].browse(self.env.uid)
            if user.has_group('hotel.group_hotel_call'):
                vals.update({
                    'to_read': True,
                    'to_assign': True,
                })
        res = super(HotelReservation, self).write(vals)
        if pricesChanged:
            for record in self:
                if record.reservation_type in ('staff', 'out'):
                    record.update({'price_unit': 0})
                record.folio_id.compute_invoices_amount()
                checkin = vals.get('checkin', record.checkin)
                checkout = vals.get('checkout', record.checkout)
                days_diff = date_utils.date_diff(checkin,
                                                 checkout, hours=False)
                rlines = record.prepare_reservation_lines(checkin, days_diff)
                record.update({
                    'reservation_line_ids': rlines['commands'],
                    'price_unit': rlines['total_price'],
                })
        return res

    # @api.multi
    # def uos_change(self, product_uos, product_uos_qty=0, product_id=None):
    #     '''
    #     @param self: object pointer
    #     '''
    #     # for folio in self:
    #     #     line = folio.order_line_id
    #     #     line.uos_change(product_uos, product_uos_qty=0,
    #     #                     product_id=None)
    #     return True

    # FIXME add room.id to on change after removing inheritance
    @api.onchange('adults', 'children')
    def check_capacity(self):
        if self.room_id:
            persons = self.adults + self.children
            if self.room_id.capacity < persons:
                self.adults = self.room_id.capacity
                self.children = 0
                raise UserError(
                    _('%s people do not fit in this room! ;)') % (persons))

    @api.onchange('room_type_id')
    # def on_change_virtual_room_id(self):
    def on_change_room_type_id(self):
        if not self.checkin:
            self.checkin = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if not self.checkout:
            self.checkout = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        days_diff = date_utils.date_diff(
            self.checkin, self.checkout, hours=False)
        rlines = self.prepare_reservation_lines(
            self.checkin,
            days_diff,
            update_old_prices=True)
        self.reservation_line_ids = rlines['commands']

        if self.reservation_type in ['staff', 'out']:
            self.price_unit = 0.0
            self.cardex_pending = 0
        else:
            self.price_unit = rlines['total_price']

    @api.onchange('checkin', 'checkout', 'room_id',
                  'reservation_type', 'room_type_id')
    def on_change_checkin_checkout_product_id(self):
        _logger.info('on_change_checkin_checkout_product_id')
        # import wdb; wdb.set_trace()
        if not self.checkin:
            self.checkin = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if not self.checkout:
            self.checkout = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        # WARNING Need a review
        # if self.product_id:
        #     self.tax_id = [(6, False, self.virtual_room_id.product_id.taxes_id.ids)]
        #     room = self.env['hotel.room'].search([
        #         ('product_id', '=', self.product_id.id)
        #     ])
        #     if self.adults == 0:
        #         self.adults = room.capacity
        #     if not self.virtual_room_id and room.price_virtual_room:
        #         self.virtual_room_id = room.price_virtual_room.id
        if self.room_id:
            # self.tax_id = [(6, False, self.room_type_id.product_id.taxes_id.ids)]
            if self.adults == 0:
                self.adults = self.room_id.capacity
            if not self.room_type_id:
                self.room_type_id = self.room_id.room_type_id
                self.tax_id = [(6, False, self.room_id.room_type_id.taxes_id.ids)]

        # UTC -> Hotel tz
        tz = self.env['ir.default'].sudo().get('res.config.settings',
                                               'tz_hotel')
        chkin_utc_dt = date_utils.get_datetime(self.checkin)
        chkout_utc_dt = date_utils.get_datetime(self.checkout)

        if self.room_type_id:
            checkin_str = chkin_utc_dt.strftime('%d/%m/%Y')
            checkout_str = chkout_utc_dt.strftime('%d/%m/%Y')
            self.name = self.room_type_id.name + ': ' + checkin_str + ' - '\
                + checkout_str
            # self.product_uom = self.product_id.uom_id

        if chkin_utc_dt >= chkout_utc_dt:
            dpt_hour = self.env['ir.default'].sudo().get(
                'res.config.settings', 'default_departure_hour')
            checkout_str = (chkin_utc_dt + timedelta(days=1)).strftime(
                DEFAULT_SERVER_DATE_FORMAT)
            checkout_str = "%s %s:00" % (checkout_str, dpt_hour)
            checkout_dt = date_utils.get_datetime(checkout_str, stz=tz)
            checkout_utc_dt = date_utils.dt_as_timezone(checkout_dt, 'UTC')
            self.checkout = checkout_utc_dt.strftime(
                DEFAULT_SERVER_DATETIME_FORMAT)

        if self.state == 'confirm' and self.checkin_is_today():
            self.is_checkin = True
            folio = self.env['hotel.folio'].browse(self.folio_id.id)
            if folio:
                folio.checkins_reservations = folio.room_lines.search_count([
                    ('folio_id', '=', folio.id), ('is_checkin', '=', True)
                ])

        if self.state == 'booking' and self.checkout_is_today():
            self.is_checkout = False
            folio = self.env['hotel.folio'].browse(self.folio_id.id)
            if folio:
                folio.checkouts_reservations = folio.room_lines.search_count([
                    ('folio_id', '=', folio.id), ('is_checkout', '=', True)
                ])

        days_diff = date_utils.date_diff(
            self.checkin, self.checkout, hours=False)
        rlines = self.prepare_reservation_lines(
            self.checkin,
            days_diff,
            update_old_prices=False)
        self.reservation_line_ids = rlines['commands']

        if self.reservation_type in ['staff', 'out']:
            self.price_unit = 0.0
            self.cardex_pending = 0
        else:
            self.price_unit = rlines['total_price']

    # FIXME add room.id to on change after removing inheritance
    @api.model
    def get_availability(self, checkin, checkout, dbchanged=True,
                         dtformat=DEFAULT_SERVER_DATE_FORMAT):
        date_start = date_utils.get_datetime(checkin)
        date_end = date_utils.get_datetime(checkout)
        # Not count end day of the reservation
        date_diff = date_utils.date_diff(date_start, date_end, hours=False)

        hotel_vroom_obj = self.env['hotel.room.type']
        # virtual_room_avail_obj = self.env['hotel.room.type.availability']

        rooms_avail = []
        # FIXME con una relacion Many2one, cada habitacion está en un solo tipo
        # por lo que la disponibilidad para la habitación se tiene que buscar
        # directamente en ese tipo
        # vrooms = hotel_vroom_obj.search([
        #     ('room_ids.product_id', '=', self.room_id)
        # ])
        # FIXME Si lo de arriba es cierto, este bucle sobra. Sólo hay un room_type_id
        for vroom in self.room_type_id:
            rdays = []
            for i in range(0, date_diff):
                ndate_dt = date_start + timedelta(days=i)
                ndate_str = ndate_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                avail = len(hotel_vroom_obj.check_availability_virtual_room(
                    ndate_str,
                    ndate_str,
                    room_type_id=vroom.id))
                if not dbchanged:
                    avail = avail - 1
                # Can be less than zero because 'avail' can not equal
                # with the real 'avail' (ex. Online Limits)
                avail = max(min(avail, vroom.total_rooms_count), 0)
                rdays.append({
                    'date': ndate_dt.strftime(dtformat),
                    'avail': avail,
                })
            ravail = {'id': vroom.id, 'days': rdays}
            rooms_avail.append(ravail)

        return rooms_avail

    @api.multi
    def prepare_reservation_lines(self, str_start_date_utc, days,
                                  update_old_prices=False):
        self.ensure_one()
        total_price = 0.0
        cmds = [(5, False, False)]
        # TO-DO: Redesign relation between hotel.reservation
        # and sale.order.line to allow manage days by units in order
        #~ if self.invoice_status == 'invoiced' and not self.splitted:
            #~ raise ValidationError(_("This reservation is already invoiced. \
                        #~ To expand it you must create a new reservation."))
        hotel_tz = self.env['ir.default'].sudo().get(
            'res.config.settings', 'hotel_tz')
        start_date_utc_dt = date_utils.get_datetime(str_start_date_utc)
        start_date_dt = date_utils.dt_as_timezone(start_date_utc_dt, hotel_tz)

        # import wdb; wdb.set_trace()

        # room = self.env['hotel.room'].search([
        #     ('product_id', '=', self.product_id.id)
        # ])
        # product_id = self.room_id.sale_price_type == 'vroom' and self.room_id.price_virtual_room.product_id
        product_id = self.room_type_id
        pricelist_id = self.env['ir.default'].sudo().get(
            'res.config.settings', 'parity_pricelist_id')
        if pricelist_id:
            pricelist_id = int(pricelist_id)
        old_lines_days = self.mapped('reservation_line_ids.date')
        for i in range(0, days):
            ndate = start_date_dt + timedelta(days=i)
            ndate_str = ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)
            _logger.info('ndate_str: %s', ndate_str)
            if update_old_prices or ndate_str not in old_lines_days:
                # prod = product_id.with_context(
                #     lang=self.partner_id.lang,
                #     partner=self.partner_id.id,
                #     quantity=1,
                #     date=ndate_str,
                #     pricelist=pricelist_id,
                #     uom=self.product_uom.id)
                prod = product_id.with_context(
                    lang=self.partner_id.lang,
                    partner=self.partner_id.id,
                    quantity=1,
                    date=ndate_str,
                    pricelist=pricelist_id)
                line_price = prod.price
            else:
                line = self.reservation_line_ids.filtered(lambda r: r.date == ndate_str)
                line_price = line.price
            cmds.append((0, False, {
                'date': ndate_str,
                'price': line_price
            }))
            total_price += line_price
        return {'total_price': total_price, 'commands': cmds}

    @api.constrains('adults')
    def check_adults(self):
        if self.adults == 0 and self.room_id:
            # room = self.env['hotel.room'].search([
            #     ('product_id', '=', self.product_id.id)
            # ], limit=1)
            self.adults = self.room_id.capacity

    @api.multi
    @api.onchange('checkin', 'checkout', 'room_type_id', 'room_id')
    def on_change_checkout(self):
        '''
        When you change checkin or checkout it will checked it
        and update the qty of hotel folio line
        -----------------------------------------------------------------
        @param self: object pointer
        '''
        _logger.info('on_change_checkout')
        self.ensure_one()
        now_utc_dt = date_utils.now()
        if not self.checkin:
            self.checkin = now_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if not self.checkout:
            now_utc_dt = date_utils.get_datetime(self.checkin)\
                + timedelta(days=1)
            self.checkout = now_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if self.overbooking:
            return
        checkout_dt = date_utils.get_datetime(self.checkout)
        occupied = self.env['hotel.reservation'].occupied(
            self.checkin,
            checkout_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)).filtered(
                lambda r: r.id != self._origin.id)
        rooms_occupied = occupied.mapped('room_id.id')
        if self.room_id and self.room_id.id in rooms_occupied:
            warning_msg = _('You tried to change \
                   reservation with room those already reserved in this \
                   reservation period')
            raise ValidationError(warning_msg)
        domain_rooms = [
            # ('isroom', '=', True),
            ('id', 'not in', rooms_occupied)
        ]
        # if self.check_rooms:
        #     if self.room_type_id:
        #         domain_rooms.append(
        #             ('categ_id.id', '=', self.room_type_id.cat_id.id)
        #         )
        #     if self.virtual_room_id:
        #         room_categories = self.virtual_room_id.room_type_ids.mapped(
        #             'cat_id.id')
        #         link_virtual_rooms = self.virtual_room_id.room_ids\
        #             | self.env['hotel.room'].search([
        #                 ('categ_id.id', 'in', room_categories)])
        #         room_ids = link_virtual_rooms.mapped('room_id.id')
        #         domain_rooms.append(('id', 'in', room_ids))
        return {'domain': {'room_id': domain_rooms}}

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

    @api.one
    def copy_data(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''
        return False
        # FIXME added for migration
        # line_id = self.order_line_id.id
        # sale_line_obj = self.env['sale.order.line'].browse(line_id)
        # return sale_line_obj.copy_data(default=default)

    @api.constrains('checkin', 'checkout', 'state', 'room_id', 'overbooking')
    def check_dates(self):
        """
        1.-When date_order is less then checkin date or
        Checkout date should be greater than the checkin date.
        3.-Check the reservation dates are not occuped
        """
        chkin_utc_dt = date_utils.get_datetime(self.checkin)
        chkout_utc_dt = date_utils.get_datetime(self.checkout)
        if chkin_utc_dt >= chkout_utc_dt:
            raise ValidationError(_('Room line Check In Date Should be \
                less than the Check Out Date!'))
        if not self.overbooking and not self._context.get("ignore_avail_restrictions", False):
            occupied = self.env['hotel.reservation'].occupied(
                self.checkin,
                chkout_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT))
            occupied = occupied.filtered(
                lambda r: r.room_id.id == self.room_id.id
                and r.id != self.id)
            occupied_name = ','.join(str(x.room_id.name) for x in occupied)
            if occupied:
                warning_msg = _('You tried to change/confirm \
                   reservation with room those already reserved in this \
                   reservation period: %s ') % occupied_name
                raise ValidationError(warning_msg)

    @api.multi
    def unlink(self):
        # for record in self:
        #     record.order_line_id.unlink()
        return super(HotelReservation, self).unlink()

    @api.model
    def occupied(self, str_checkin_utc, str_checkout_utc):
        """
        Return a RESERVATIONS array between in and out parameters
        IMPORTANT: This function should receive the dates in UTC datetime zone,
                    as String format
        """
        tz_hotel = self.env['ir.default'].sudo().get(
                                        'res.config.settings', 'tz_hotel')
        checkin_utc_dt = date_utils.get_datetime(str_checkin_utc)
        checkin_dt = date_utils.dt_as_timezone(checkin_utc_dt, tz_hotel)
        days_diff = date_utils.date_diff(str_checkin_utc, str_checkout_utc,
                                         hours=False)
        dates_list = date_utils.generate_dates_list(checkin_dt, days_diff or 1,
                                                    stz=tz_hotel)
        reservations = self.env['hotel.reservation'].search([
            ('reservation_line_ids.date', 'in', dates_list),
            ('state', '!=', 'cancelled'),
            ('overbooking', '=', False)
        ])
        return reservations
