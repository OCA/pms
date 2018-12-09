# Copyright 2017-2018  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
import time
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import (
    misc,
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
_logger = logging.getLogger(__name__)


class HotelReservation(models.Model):
    _name = 'hotel.reservation'
    _description = 'Hotel Reservation'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = "last_updated_res desc, name"

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
            return (fields.Date.from_string(today) + timedelta(days=1)).strftime(
                DEFAULT_SERVER_DATE_FORMAT)

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
                record.shared_folio = len(record.folio_id.room_lines) > 1 or \
                        any(record.folio_id.service_ids.filtered(
                            lambda x: x.ser_room_line.id != record.id))

    @api.depends('checkin', 'checkout')
    def _computed_nights(self):
        for res in self:
            if res.checkin and res.checkout:
                res.nights = (
                    fields.Date.from_string(res.checkout) - fields.Date.from_string(res.checkin)
                ).days

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
    board_service_id = fields.Many2one('hotel.board.service', string='Board Service')
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
    closure_reason_id = fields.Many2one(related='folio_id.closure_reason_id')
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
    service_ids = fields.One2many('hotel.service', 'ser_room_line')

    pricelist_id = fields.Many2one('product.pricelist',
                                   related='folio_id.pricelist_id',
                                   readonly="1")
    checkin_partner_ids = fields.One2many('hotel.checkin.partner', 'reservation_id')
    # TODO: As checkin_partner_count is a computed field, it can't not be used in a domain filer
    # Non-stored field hotel.reservation.checkin_partner_count cannot be searched
    # searching on a computed field can also be enabled by setting the search parameter.
    # The value is a method name returning a Domains
    checkin_partner_count = fields.Integer('Checkin counter',
                                  compute='_compute_checkin_partner_count')
    checkin_partner_pending_count = fields.Integer('Checkin Pending Num',
                                          compute='_compute_checkin_partner_count',
                                          search='_search_checkin_partner_pending')
    # check_rooms = fields.Boolean('Check Rooms')
    splitted = fields.Boolean('Splitted', default=False)
    parent_reservation = fields.Many2one('hotel.reservation',
                                         'Parent Reservation')
    overbooking = fields.Boolean('Is Overbooking', default=False)
    reselling = fields.Boolean('Is Reselling', default=False)

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
    tax_id = fields.Many2many('account.tax',
                              string='Taxes',
                              domain=['|', ('active', '=', False), ('active', '=', True)])
    # qty_to_invoice = fields.Float(
    #     string='To Invoice', store=True, readonly=True,
    #     digits=dp.get_precision('Product Unit of Measure'))
    # qty_invoiced = fields.Float(
    #     compute='_get_invoice_qty', string='Invoiced', store=True, readonly=True,
    #     digits=dp.get_precision('Product Unit of Measure'))
    # qty_delivered = fields.Float(string='Delivered', copy=False, digits=dp.get_precision('Product Unit of Measure'), default=0.0)
    # qty_delivered_updateable = fields.Boolean(compute='_compute_qty_delivered_updateable', string='Can Edit Delivered', readonly=True, default=True)
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
    # FIXME discount per night
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)

    # analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')

    @api.model
    def create(self, vals):
        if 'room_id' not in vals:
            vals.update(self._autoassign(vals))
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
        vals.update({
            'last_updated_res': fields.Datetime.now(),
        })
        if 'board_service_id' in vals:
                board_services = []
                board = self.env['hotel.board.service'].browse(vals['board_service_id'])
                for product in board.service_ids:
                    board_services.append((0, False, {
                        'product_id': product.id,
                        'is_board_service': True,
                        }))
                vals.update({'service_ids': board_services})
        if self.compute_price_out_vals(vals):
            days_diff = (
                fields.Date.from_string(vals['checkout']) - fields.Date.from_string(vals['checkin'])
            ).days
            vals.update(self.prepare_reservation_lines(
                vals['checkin'],
                days_diff,
                vals=vals)) #REVISAR el unlink
        record = super(HotelReservation, self).create(vals)
        #~ if (record.state == 'draft' and record.folio_id.state == 'sale') or \
                #~ record.preconfirm:
            #~ record.confirm()
        return record

    @api.multi
    def write(self, vals):
        if self.notify_update(vals):
            vals.update({
                'last_updated_res': fields.Datetime.now()
            })
        for record in self:
            checkin = vals['checkin'] if 'checkin' in vals else record.checkin
            checkout = vals['checkout'] if 'checkout' in vals else record.checkout
            days_diff = (
                fields.Date.from_string(checkout) - \
                fields.Date.from_string(checkin)
            ).days
            if self.compute_board_services(vals):
                record.service_ids.filtered(lambda r: r.is_board_service == True).unlink()
                board_services = []
                board = self.env['hotel.board.service'].browse(vals['board_service_id'])
                for product in board.service_ids:
                    board_services.append((0, False, {
                        'product_id': product.id,
                        'is_board_service': True,
                        }))
                # NEED REVIEW: Why I need add manually the old IDs if board service is (0,0,(-)) ¿?¿?¿
                record.update({'service_ids':  [(6, 0, record.service_ids.ids)] + board_services})
                update_services = record.service_ids.filtered(
                    lambda r: r.is_board_service == True
                )
                for service in update_services:
                    service.onchange_product_calc_qty()
            if record.compute_price_out_vals(vals):
                record.update(record.prepare_reservation_lines(
                    checkin,
                    days_diff,
                    vals=vals)) #REVISAR el unlink
            if record.compute_qty_service_day(vals):
                for service in record.service_ids:
                    if service.product_id.per_day:
                        service.update(service.prepare_service_lines(
                            dfrom=checkin,
                            days=days_diff,
                            per_person=service.product_id.per_person,
                            persons=service.ser_room_line.adults,
                            old_line_days=service.service_line_ids
                            ))
            if ('checkin' in vals and record.checkin != vals['checkin']) or \
                ('checkout' in vals and record.checkout != vals['checkout']) or \
                ('state' in vals and record.state != vals['state']):
                    record.update({'to_send': True})
        res = super(HotelReservation, self).write(vals)
        return res

    @api.multi
    def compute_board_services(self, vals):
        """
        We must compute service_ids when we hace a board_service_id without
        service_ids associated to reservation
        """
        if 'board_service_id' in vals:
            if 'service_ids' in vals:
                for service in vals['service_ids']:
                    if 'is_board_service' in service[2] and \
                        service[2]['is_board_service'] == True:
                            return False
            return True
        return False

    @api.multi
    def compute_qty_service_day(self, vals):
        """
        Compute if It is necesary calc price in write/create
        """
        self.ensure_one()
        if not vals:
            vals = {}
        if 'service_ids' in vals:
            return False
        if ('checkin' in vals and self.checkin != vals['checkin']) or \
                ('checkout' in vals and self.checkout != vals['checkout']) or \
                ('adults' in vals and self.checkout != vals['adults']):
            return True
        return False

    @api.model
    def _prepare_add_missing_fields(self, values):
        """ Deduce missing required fields from the onchange """
        res = {}
        onchange_fields = ['room_id', 'reservation_type',
            'currency_id', 'name', 'board_service_id']
        if values.get('room_type_id'):
            line = self.new(values)
            if any(f not in values for f in onchange_fields):
                line.onchange_room_id()
                line.onchange_compute_reservation_description()
                line.onchange_board_service()
            if 'pricelist_id' not in values:
                line.onchange_partner_id()
            for field in onchange_fields:
                if field not in values:
                    res[field] = line._fields[field].convert_to_write(line[field], line)
        return res

    @api.model
    def _autoassign(self, values):
        res = {}
        checkin = values.get('checkin') 
        checkout = values.get('checkout')
        room_type = values.get('room_type_id')
        if checkin and checkout and room_type:
            room_chosen = self.env['hotel.room.type'].check_availability_room_type(checkin, checkout, room_type)[0]
            # Check room_chosen exist
            res.update({
                'room_id': room_chosen.id
            })
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
        self.overbooking = not self.overbooking

    @api.multi
    def open_folio(self):
        action = self.env.ref('hotel.open_hotel_folio1_form_tree_all').read()[0]
        if self.folio_id:
            action['views'] = [(self.env.ref('hotel.hotel_folio_view_form').id, 'form')]
            action['res_id'] = self.folio_id.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def open_reservation_form(self):
        action = self.env.ref('hotel.open_hotel_reservation_form_tree_all').read()[0]
        action['views'] = [(self.env.ref('hotel.hotel_reservation_view_form').id, 'form')]
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
            'reselling': self.reselling,
            'price_unit': self.price_unit,
            'splitted': self.splitted,
            # 'room_type_id': self.room_type_id.id,
            'room_type_id': self.room_type_id.id,
        }

    @api.constrains('adults')
    def _check_adults(self):
        for record in self:
            extra_bed = record.service_ids.filtered(    
                        lambda r: r.product_id.is_extra_bed == True)
            if record.adults > record.room_id.get_capacity(len(extra_bed)):
                raise ValidationError(
                    _("Reservation persons can't be higher than room capacity"))
            if record.adults == 0:
                raise ValidationError(_("Reservation has no adults"))

    """
    ONCHANGES ----------------------------------------------------------
    """

    @api.onchange('adults', 'room_id')
    def onchange_room_id(self):
        if self.room_id:
            write_vals = {}
            extra_bed = self.service_ids.filtered(
                        lambda r: r.product_id.is_extra_bed == True)
            if self.room_id.get_capacity(len(extra_bed)) < self.adults:
                raise UserError(
                    _('%s people do not fit in this room! ;)') % (self.adults))
            if self.adults == 0:
                write_vals.update({'adults': self.room_id.capacity})
            #Si el registro no existe, modificar room_type aunque ya esté establecido
            if not self.room_type_id:
                write_vals.update({'room_type_id': self.room_id.room_type_id.id})
            self.update(write_vals)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        pricelist = self.partner_id.property_product_pricelist and \
                self.partner_id.property_product_pricelist.id or \
                self.env['ir.default'].sudo().get('res.config.settings', 'default_pricelist_id')
        values = {
            'pricelist_id': pricelist,
        }
        self.update(values)

    @api.multi
    @api.onchange('pricelist_id')
    def onchange_pricelist_id(self):
        values = {'reservation_type': self.env['hotel.folio'].calcule_reservation_type(
                                       self.pricelist_id.is_staff,
                                       self.reservation_type)}
        self.update(values)

    @api.onchange('reservation_type')
    def assign_partner_company_on_out_service(self):
        if self.reservation_type == 'out':
            self.update({'partner_id': self.env.user.company_id.partner_id.id})

    # When we need to overwrite the prices even if they were already established
    @api.onchange('room_type_id', 'pricelist_id', 'reservation_type')
    def onchange_overwrite_price_by_day(self):
        if self.room_type_id and self.checkin and self.checkout:
            days_diff = (
                fields.Date.from_string(self.checkout) - fields.Date.from_string(self.checkin)
            ).days
            self.update(self.prepare_reservation_lines(
                self.checkin,
                days_diff,
                update_old_prices=True))

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
            self.checkout = (fields.Date.from_string(self.checkin) + timedelta(days=1)).strftime(
                DEFAULT_SERVER_DATE_FORMAT)
        if self.room_type_id:
            days_diff = (
                fields.Date.from_string(self.checkout) - fields.Date.from_string(self.checkin)
            ).days
            self.update(self.prepare_reservation_lines(
                self.checkin,
                days_diff,
                update_old_prices=False))

    @api.onchange('checkin', 'checkout', 'room_type_id')
    def onchange_compute_reservation_description(self):
        if self.room_type_id and self.checkin and self.checkout:
            checkin_dt = fields.Date.from_string(self.checkin)
            checkout_dt = fields.Date.from_string(self.checkout)
            checkin_str = checkin_dt.strftime('%d/%m/%Y')
            checkout_str = checkout_dt.strftime('%d/%m/%Y')
            self.name = self.room_type_id.name + ': ' + checkin_str + ' - '\
                + checkout_str

    @api.onchange('checkin', 'checkout')
    def onchange_update_service_per_day(self):
        services = self.service_ids.filtered(lambda r: r.per_day == True)
        for service in services:
            service.onchange_product_calc_qty()

    @api.multi
    @api.onchange('checkin', 'checkout', 'room_id')
    def onchange_room_availabiltiy_domain(self):
        self.ensure_one()
        if self.checkin and self.checkout:
            if self.overbooking or self.reselling:
                return
            occupied = self.env['hotel.reservation'].get_reservations(
                self.checkin,
                fields.Date.from_string(self.checkout).strftime(
                    DEFAULT_SERVER_DATE_FORMAT)).filtered(
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

    @api.onchange('board_service_id')
    def onchange_board_service(self):
        if self.board_service_id:
            board_services = []
            for product in self.board_service_id.service_ids:
                if product.per_day:
                    vals = {
                        'product_id': product.id,
                        'is_board_service': True,
                        }
                    vals.update(self.env['hotel.service'].prepare_service_lines(
                        dfrom=self.checkin,
                        days=self.nights,
                        per_person=product.per_person,
                        persons=self.adults,
                        old_line_days=False))                    
                    board_services.append((0, False, vals))
            other_services = self.service_ids.filtered(lambda r: r.is_board_service == False)
            
            self.update({'service_ids':  [(6, 0, other_services.ids)] + board_services})

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
        for record in self:
            vals = {}
            if record.checkin_partner_ids:
                vals.update({'state': 'booking'})
            else:
                vals.update({'state': 'confirm'})
            record.write(vals)

            if record.splitted:
                master_reservation = record.parent_reservation or record
                splitted_reservs = hotel_reserv_obj.search([
                    ('splitted', '=', True),
                    '|',
                    ('parent_reservation', '=', master_reservation.id),
                    ('id', '=', master_reservation.id),
                    ('folio_id', '=', record.folio_id.id),
                    ('id', '!=', record.id),
                    ('state', '!=', 'confirm')
                ])
                splitted_reservs.confirm()
        return True

    @api.multi
    def button_done(self):
        '''
        @param self: object pointer
        '''
        for record in self:
            record.action_reservation_checkout()
        return True

    @api.multi
    def action_cancel(self):
        for record in self:
            record.write({
                'state': 'cancelled',
                'discount': 100.0,
            })
            if record.splitted:
                master_reservation = record.parent_reservation or record
                splitted_reservs = self.env['hotel.reservation'].search([
                    ('splitted', '=', True),
                    '|',
                    ('parent_reservation', '=', master_reservation.id),
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
            record.state = 'draft'
            if record.splitted:
                master_reservation = record.parent_reservation or record
                splitted_reservs = self.env['hotel.reservation'].search([
                    ('splitted', '=', True),
                    '|',
                    ('parent_reservation', '=', master_reservation.id),
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
        for record in self:
            amount_room = sum(record.reservation_line_ids.mapped('price'))
            if amount_room > 0:
                product = record.room_type_id.product_id
                price = amount_room * (1 - (record.discount or 0.0) * 0.01)
                taxes = record.tax_id.compute_all(price, record.currency_id, 1, product=product)
                record.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })

    @api.model
    def prepare_reservation_lines(self, dfrom, days, vals=False, update_old_prices=False):
        total_price = 0.0
        cmds = [(5, 0, 0)]
        if not vals:
            vals = {}
        pricelist_id = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_pricelist_id')
        #~ pricelist_id = vals.get('pricelist_id') or self.pricelist_id.id
        room_type_id = vals.get('room_type_id') or self.room_type_id.id
        product = self.env['hotel.room.type'].browse(room_type_id).product_id
        old_lines_days = self.mapped('reservation_line_ids.date') #TODO: This is a
        # PROBLEM when self is multirecord and the records has different old lines
        partner = self.env['res.partner'].browse(vals.get('partner_id') or self.partner_id.id)
        for i in range(0, days):
            idate = (fields.Date.from_string(dfrom) + timedelta(days=i)).strftime(
                DEFAULT_SERVER_DATE_FORMAT)
            old_line = self.reservation_line_ids.filtered(lambda r: r.date == idate)
            if update_old_prices or (idate not in old_lines_days):
                product = product.with_context(
                    lang=partner.lang,
                    partner=partner.id,
                    quantity=1,
                    date=idate,
                    pricelist=pricelist_id,
                    uom=product.uom_id.id)
                line_price = self.env['account.tax']._fix_tax_included_price_company(
                    product.price, product.taxes_id, self.tax_id, self.company_id)
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
        view_id = self.env.ref('hotel.account_payment_view_form_folio').id
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
        domain = self._get_domain_reservations_occupation(dfrom, dto)
        return self.env['hotel.reservation'].search(domain)

    @api.model
    def _get_domain_reservations_occupation(self, dfrom, dto):
        domain = [('reservation_line_ids.date', '>=', dfrom),
                  ('reservation_line_ids.date', '<', dto),
                  ('state', '!=', 'cancelled'),
                  ('overbooking', '=', False),
                  ('reselling', '=', False),]
        return domain

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
    @api.constrains('checkin', 'checkout', 'state', 'room_id', 'overbooking', 'reselling')
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
    def _compute_checkin_partner_count(self):
        _logger.info('_compute_checkin_partner_count')
        for record in self:
            record.checkin_partner_count = len(record.checkin_partner_ids)
            record.checkin_partner_pending_count = (record.adults + record.children) \
                    - len(record.checkin_partner_ids)

    # https://www.odoo.com/es_ES/forum/ayuda-1/question/calculated-fields-in-search-filter-possible-118501
    @api.multi
    def _search_checkin_partner_pending(self, operator, value):
        self.ensure_one()
        recs = self.search([]).filtered(lambda x: x.checkin_partner_pending_count > 0)
        return [('id', 'in', [x.id for x in recs])] if recs else []

    @api.multi
    def action_reservation_checkout(self):
        for record in self:
            record.state = 'done'

    @api.multi
    def action_checks(self):
        self.ensure_one()
        return {
            'name': _('Checkins'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hotel.checkin.partner',
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
