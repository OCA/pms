# Copyright 2018 Dario Lodeiros
# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import time
import logging
from datetime import timedelta
from openerp.exceptions import ValidationError
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
from openerp import models, fields, api, _
from odoo.addons.hotel import date_utils
import odoo.addons.decimal_precision as dp
_logger = logging.getLogger(__name__)


class FolioWizard(models.TransientModel):
    _name = 'hotel.folio.wizard'

    @api.model
    def _get_default_center_user(self):
        user = self.env['res.users'].browse(self.env.uid)
        return user.has_group('hotel.group_hotel_call')

    @api.model
    def _get_default_checkin(self):
        folio = False
        default_arrival_hour = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_arrival_hour')
        if 'folio_id' in self._context:
            folio = self.env['hotel.folio'].search([
                ('id', '=', self._context['folio_id'])
            ])
        if folio and folio.room_lines:
            return folio.room_lines[0].checkin
        else:
            tz_hotel = self.env['ir.default'].sudo().get(
                'res.config.settings', 'tz_hotel')
            now_utc_dt = date_utils.now()
            ndate = "%s %s:00" % \
                (now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                 default_arrival_hour)
            ndate_dt = date_utils.get_datetime(ndate, stz=tz_hotel)
            ndate_dt = date_utils.dt_as_timezone(ndate_dt, 'UTC')
            return ndate_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def _get_default_checkout(self):
        folio = False
        default_departure_hour = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_departure_hour')
        if 'folio_id' in self._context:
            folio = self.env['hotel.folio'].search([
                ('id', '=', self._context['folio_id'])
            ])
        if folio and folio.room_lines:
            return folio.room_lines[0].checkout
        else:
            tz_hotel = self.env['ir.default'].sudo().get(
                'res.config.settings', 'tz_hotel')
            now_utc_dt = date_utils.now() + timedelta(days=1)
            ndate = "%s %s:00" % \
                (now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                 default_departure_hour)
            ndate_dt = date_utils.get_datetime(ndate, stz=tz_hotel)
            ndate_dt = date_utils.dt_as_timezone(ndate_dt, 'UTC')
            return ndate_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def _get_default_channel_type(self):
        user = self.env['res.users'].browse(self.env.uid)
        if user.has_group('hotel.group_hotel_call'):
            return 'phone'

    partner_id = fields.Many2one('res.partner',string="Customer")
    checkin = fields.Datetime('Check In', required=True,
                              default=_get_default_checkin)
    checkout = fields.Datetime('Check Out', required=True,
                               default=_get_default_checkout)
    reservation_wizard_ids = fields.One2many('hotel.reservation.wizard',
                                             'folio_wizard_id',
                                             string="Resevations")
    service_wizard_ids = fields.One2many('hotel.service.wizard',
                                         'folio_wizard_id',
                                         string='Services')
    total = fields.Float('Total', compute='_computed_total')
    confirm = fields.Boolean('Confirm Reservations', default="1")
    autoassign = fields.Boolean('Autoassign', default="1")
    channel_type = fields.Selection([
        ('door', 'Door'),
        ('mail', 'Mail'),
        ('phone', 'Phone')
    ], string='Sales Channel', default=_get_default_channel_type)
    room_type_wizard_ids = fields.Many2many('hotel.room.type.wizard',
                                            string="Virtual Rooms")
    call_center = fields.Boolean(default=_get_default_center_user)

    def assign_rooms(self):
        self.assign = True

    @api.onchange('autoassign')
    def create_reservations(self):
        self.ensure_one()
        total = 0
        cmds = []
        for line in self.room_type_wizard_ids:
            if line.rooms_num == 0:
                continue
            if line.rooms_num > line.max_rooms:
                raise ValidationError(_("Too many rooms!"))
            elif line.room_type_id:
                checkout_dt = date_utils.get_datetime(line.checkout)
                occupied = self.env['hotel.reservation'].occupied(
                    line.checkin,
                    checkout_dt.strftime(DEFAULT_SERVER_DATE_FORMAT))
                rooms_occupied = occupied.mapped('product_id.id')
                free_rooms = self.env['hotel.room'].search([
                    ('product_id.id', 'not in', rooms_occupied),
                    ('price_room_type.id', '=', line.room_type_id.id)
                ], order='sequence', limit=line.rooms_num)
                room_ids = free_rooms.mapped('product_id.id')
                product_list = self.env['product.product'].search([
                    ('id', 'in', room_ids)
                ])
                nights = date_utils.date_diff(line.checkin,
                                              line.checkout,
                                              hours=False)
                hotel_tz = self.env['ir.default'].sudo().get(
                    'res.config.settings',
                    'hotel_tz')
                start_date_utc_dt = date_utils.get_datetime(self.checkin)
                start_date_dt = date_utils.dt_as_timezone(start_date_utc_dt,
                                                          hotel_tz)
                for room in product_list:
                    pricelist_id = self.env['ir.default'].sudo().get(
                        'res.config.settings', 'parity_pricelist_id')
                    if pricelist_id:
                        pricelist_id = int(pricelist_id)
                    res_price = 0
                    for i in range(0, nights):
                        ndate = start_date_dt + timedelta(days=i)
                        ndate_str = ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)
                        prod = line.room_type_id.product_id.with_context(
                            lang=self.partner_id.lang,
                            partner=self.partner_id.id,
                            quantity=1,
                            date=ndate_str,
                            pricelist=pricelist_id,
                            uom=room.uom_id.id)
                        res_price += prod.price
                    adults = self.env['hotel.room'].search([
                        ('product_id.id', '=', room.id)
                    ]).capacity
                    res_price = res_price - (res_price * line.discount)/100
                    total += res_price
                    cmds.append((0, False, {
                        'checkin': line.checkin,
                        'checkout': line.checkout,
                        'discount': line.discount,
                        'product_id': room.id,
                        'nights': nights,
                        'adults': adults,
                        'children': 0,
                        'room_type_id': line.room_type_id,
                        'price': res_price,
                        'amount_reservation': res_price
                    }))
        self.reservation_wizard_ids = cmds
        self.total = total

    @api.multi
    @api.onchange('checkin', 'checkout')
    def onchange_checks(self):
        '''
        When you change checkin or checkout it will checked it
        and update the qty of hotel folio line
        -----------------------------------------------------------------
        @param self: object pointer
        '''
        self.ensure_one()
        if not self.checkin:
            self.checkin = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if not self.checkout:
            self.checkout = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        # UTC -> Hotel tz
        tz = self.env['ir.default'].sudo().get('res.config.settings',
                                               'tz_hotel')
        chkin_utc_dt = date_utils.get_datetime(self.checkin)
        chkout_utc_dt = date_utils.get_datetime(self.checkout)

        if chkin_utc_dt >= chkout_utc_dt:
            dpt_hour = self.env['ir.default'].sudo().get(
                'res.config.settings', 'default_departure_hour')
            checkout_str = (chkin_utc_dt + timedelta(days=1)).strftime(
                DEFAULT_SERVER_DATE_FORMAT)
            checkout_str = "%s %s:00" % (checkout_str, dpt_hour)
            checkout_dt = date_utils.get_datetime(checkout_str, stz=tz)
            checkout_utc_dt = date_utils.dt_as_timezone(checkout_dt, 'UTC')
            self.checkout = checkout_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        checkout_dt = date_utils.get_datetime(self.checkout, stz=tz)
        # Reservation end day count as free day. Not check it
        checkout_dt -= timedelta(days=1)
        room_type_ids = self.env['hotel.room.type'].search([])
        room_types = []

        for room_type in room_type_ids:
            room_types.append((0, False, {
                'room_type_id': room_type.id,
                'checkin': self.checkin,
                'checkout': self.checkout,
                'folio_wizard_id': self.id,
            }))
        self.room_type_wizard_ids = room_types
        for room_type in self.room_type_wizard_ids:
            room_type.update_price()

    @api.depends('room_type_wizard_ids','reservation_wizard_ids','service_wizard_ids')
    def _computed_total(self):
        total = 0
        for line in self.service_wizard_ids:
            total += line.price_total
        if not self.reservation_wizard_ids:
            for line in self.room_type_wizard_ids:
                total += line.total_price
            self.total = total
        else:
            for line in self.reservation_wizard_ids:
                total += line.price
            self.total = total

    @api.multi
    def create_folio(self):
        self.ensure_one()
        if not self.partner_id:
            raise ValidationError(_("We need know the customer!"))
        reservations = [(5, False, False)]
        services = [(5, False, False)]
        if self.autoassign == True:
            self.create_reservations()
        for line in self.reservation_wizard_ids:
            reservations.append((0, False, {
                'product_id': line.product_id.id,
                'adults': line.adults,
                'children': line.children,
                'checkin': line.checkin,
                'checkout': line.checkout,
                'discount': line.discount,
                'room_type_id': line.room_type_id.id,
                'to_read': line.to_read, #REFACT: wubook module
                'to_assign': line.to_assign,
            }))
        for line in self.service_wizard_ids:
            services.append((0, False, {
                'product_id': line.product_id.id,
                'discount': line.discount,
                'price_unit': line.price_unit,
                'product_uom_qty': line.product_uom_qty,
            }))
        vals = {
            'partner_id': self.partner_id.id,
            'channel_type': self.channel_type,
            'room_lines': reservations,
            'service_lines': services,
        }
        newfol = self.env['hotel.folio'].create(vals)
        for room in newfol.room_lines:
            room.on_change_checkin_checkout_product_id()
        newfol.compute_invoices_amount()
        if self.confirm:
            newfol.room_lines.confirm()
        action = self.env.ref('hotel.open_hotel_folio1_form_tree_all').read()[0]
        if newfol:
            action['views'] = [(self.env.ref('hotel.view_hotel_folio1_form').id, 'form')]
            action['res_id'] = newfol.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


class HotelRoomTypeWizards(models.TransientModel):
    _name = 'hotel.room.type.wizard'

    @api.multi
    def _get_default_checkin(self):
        return self.folio_wizard_id.checkin

    @api.model
    def _get_default_checkout(self):
        return self.folio_wizard_id.checkout

    room_type_id = fields.Many2one('hotel.room.type',
                                   string="Virtual Rooms")
    rooms_num = fields.Integer('Number of Rooms')
    max_rooms = fields.Integer('Max', compute="_compute_max")
    price = fields.Float(string='Price by Room')
    total_price = fields.Float(string='Total Price')
    folio_wizard_id = fields.Many2one('hotel.folio.wizard')
    amount_reservation = fields.Float(string='Total', readonly=True)
    discount = fields.Float('discount')
    min_stay = fields.Integer('Min. Days', compute="_compute_max")
    checkin = fields.Datetime('Check In', required=True,
                              default=_get_default_checkin)
    checkout = fields.Datetime('Check Out', required=True,
                               default=_get_default_checkout)
    can_confirm = fields.Boolean(compute="_can_confirm")

    def _can_confirm(self):
        for room_type in self:
            date_start = date_utils.get_datetime(room_type.checkin)
            date_end = date_utils.get_datetime(room_type.checkout)
            date_diff = date_utils.date_diff(date_start, date_end, hours=False)
            room_type.can_confirm = room_type.max_rooms > 0 and room_type.min_stay <= date_diff

    def _compute_max(self):
        for res in self:
            user = self.env['res.users'].browse(self.env.uid)
            date_start = date_utils.get_datetime(res.checkin)
            date_end = date_utils.get_datetime(res.checkout)
            date_diff = date_utils.date_diff(date_start, date_end, hours=False)
            minstay_restrictions = self.env['hotel.room.type.restriction.item'].search([
                ('room_type_id','=',res.room_type_id.id),
            ])
            avail_restrictions = self.env['hotel.room.type.availability'].search([
                ('room_type_id','=',res.room_type_id.id)
            ])
            real_max = len(res.room_type_id.check_availability_room(
                res.checkin,
                res.checkout,
                res.room_type_id.id))
            avail = 100000
            min_stay = 0
            dates = []
            for i in range(0, date_diff):
                ndate_dt = date_start + timedelta(days=i)
                ndate_str = ndate_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                dates.append(ndate_str)
                if minstay_restrictions:
                    date_min_days = minstay_restrictions.filtered(
                        lambda r: r.date_start <= ndate_str and \
                            r.date_end >= ndate_str).min_stay
                    if date_min_days > min_stay:
                        min_stay = date_min_days
                if user.has_group('hotel.group_hotel_call'):
                    if avail_restrictions:
                        max_avail = avail_restrictions.filtered(
                            lambda r: r.date == ndate_str).wmax_avail
                        if max_avail < avail:
                            avail = min(max_avail, real_max)
                else:
                    avail = real_max


            if 100000 < avail > 0:
                res.max_rooms = avail
            else:
                res.max_rooms = 0
            if min_stay > 0:
                res.min_stay = min_stay

    @api.onchange('rooms_num', 'discount', 'price', 'room_type_id', 'checkin', 'checkout')
    def update_price(self):
        for record in self:
            checkin = record.checkin or record.folio_wizard_id.checkin
            checkout = record.checkout or record.folio_wizard_id.checkout
            if record.rooms_num > record.max_rooms:
                raise ValidationError(_("There are not enough rooms!"))
            # UTC -> Hotel tz
            tz = self.env['ir.default'].sudo().get('res.config.settings',
                                                   'tz_hotel')
            chkin_utc_dt = date_utils.get_datetime(checkin)
            chkout_utc_dt = date_utils.get_datetime(checkout)

            if chkin_utc_dt >= chkout_utc_dt:
                dpt_hour = self.env['ir.default'].sudo().get(
                    'res.config.settings', 'default_departure_hour')
                checkout_str = (chkin_utc_dt + timedelta(days=1)).strftime(
                    DEFAULT_SERVER_DATE_FORMAT)
                checkout_str = "%s %s:00" % (checkout_str, dpt_hour)
                checkout_dt = date_utils.get_datetime(checkout_str, stz=tz)
                checkout_utc_dt = date_utils.dt_as_timezone(checkout_dt, 'UTC')
                checkout = checkout_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            checkout_dt = date_utils.get_datetime(checkout, stz=tz)
            # Reservation end day count as free day. Not check it
            checkout_dt -= timedelta(days=1)
            nights = date_utils.date_diff(checkin, checkout, hours=False)
            start_date_dt = date_utils.dt_as_timezone(chkin_utc_dt, tz)
            # Reservation end day count as free day. Not check it
            checkout_dt -= timedelta(days=1)

            pricelist_id = self.env['ir.default'].sudo().get(
                'res.config.settings', 'parity_pricelist_id')
            if pricelist_id:
                pricelist_id = int(pricelist_id)

            res_price = 0
            for i in range(0, nights):
                ndate = start_date_dt + timedelta(days=i)
                ndate_str = ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)
                prod = record.room_type_id.product_id.with_context(
                    lang=record.folio_wizard_id.partner_id.lang,
                    partner=record.folio_wizard_id.partner_id.id,
                    quantity=1,
                    date=ndate_str,
                    pricelist=pricelist_id,
                    uom=record.room_type_id.product_id.uom_id.id)
                res_price += prod.price

            price = (res_price * record.discount) * 0.01
            total_price = record.rooms_num * price
            record.write({
                'checkin': checkin,
                'checkout': checkout,
                'price': price,
                'total_price': total_price,
                'amount_reservation': total_price,
            })


class ReservationWizard(models.TransientModel):
    _name = 'hotel.reservation.wizard'

    product_id = fields.Many2one('product.product',
                                 string="Room Types")

    folio_wizard_id = fields.Many2one('hotel.folio.wizard')

    adults = fields.Integer('Adults',
                            help='List of adults there in guest list. ')
    children = fields.Integer('Children',
                              help='Number of children there in guest list.')
    checkin = fields.Datetime('Check In', required=True)
    checkout = fields.Datetime('Check Out', required=True)
    room_type_id = fields.Many2one('hotel.room.type',
                                   string='Virtual Room Type',
                                   required=True)
    nights = fields.Integer('Nights', readonly=True)
    price = fields.Float(string='Total')
    amount_reservation = fields.Float(string='Total', readonly=True)
    partner_id = fields.Many2one(related='folio_wizard_id.partner_id')
    discount = fields.Float('discount')
    to_read = fields.Boolean(compute="_compute_to_read_assign")
    to_assign = fields.Boolean(compute="_compute_to_read_assign")

    @api.multi
    def _compute_to_read_assign(self):
        for rec in self:
            user = self.env['res.users'].browse(self.env.uid)
            if user.has_group('hotel.group_hotel_call'):
                rec.to_read = rec.to_assign = True

    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        for line in self:
            if line.checkin and line.checkout:
                room = self.env['hotel.room'].search([
                    ('product_id.id', '=', line.product_id.id)
                ])
                if line.adults == 0:
                    line.adults = room.capacity
                line.room_type_id = room.price_room_type.id
                checkout_dt = date_utils.get_datetime(line.checkout)
                checkout_dt -= timedelta(days=1)
                occupied = self.env['hotel.reservation'].occupied(
                    line.checkin,
                    checkout_dt.strftime(DEFAULT_SERVER_DATE_FORMAT))
                rooms_occupied = occupied.mapped('product_id.id')
                if line.product_id.id in rooms_occupied:
                    raise ValidationError(_("This room is occupied!, please, \
                        choice other room or change the reservation date"))

    @api.multi
    @api.onchange('checkin', 'checkout', 'room_type_id', 'discount')
    def onchange_dates(self):
        for line in self:
            if not self.checkin:
                self.checkin = self.folio_wizard_id.checkin
            if not self.checkout:
                self.checkout = self.folio_wizard_id.checkout

            hotel_tz = self.env['ir.default'].sudo().get(
                'res.config.settings', 'hotel_tz')
            start_date_utc_dt = date_utils.get_datetime(line.checkin)
            start_date_dt = date_utils.dt_as_timezone(start_date_utc_dt,
                                                      hotel_tz)

            if line.room_type_id:
                pricelist_id = self.env['ir.default'].sudo().get(
                    'res.config.settings', 'parity_pricelist_id')
                if pricelist_id:
                    pricelist_id = int(pricelist_id)
                nights = date_utils.date_diff(line.checkin,
                                              line.checkout,
                                              hours=False)
                res_price = 0
                for i in range(0, nights):
                    ndate = start_date_dt + timedelta(days=i)
                    ndate_str = ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    prod = line.room_type_id.product_id.with_context(
                        lang=self.partner_id.lang,
                        partner=self.partner_id.id,
                        quantity=1,
                        date=ndate_str,
                        pricelist=pricelist_id,
                        uom=line.product_id.uom_id.id)
                    res_price += prod.price
                res_price = res_price - (res_price * self.discount) * 0.01
                line.amount_reservation = res_price
                line.price = res_price
            checkout_dt = date_utils.get_datetime(self.checkout)
            checkout_dt -= timedelta(days=1)
            occupied = self.env['hotel.reservation'].occupied(
                self.checkin,
                checkout_dt.strftime(DEFAULT_SERVER_DATE_FORMAT))
            rooms_occupied = occupied.mapped('product_id.id')
            domain_rooms = [
                ('isroom', '=', True),
                ('id', 'not in', rooms_occupied)
            ]
            return {'domain': {'product_id': domain_rooms}}


class ServiceWizard(models.TransientModel):
    _name = 'hotel.service.wizard'

    product_id = fields.Many2one('product.product',
                                 string="Service")
    folio_wizard_id = fields.Many2one('hotel.folio.wizard')
    discount = fields.Float('discount')
    price_unit = fields.Float('Unit Price', required=True,
                              digits=dp.get_precision('Product Price'),
                              default=0.0)
    price_total = fields.Float(compute='_compute_amount', string='Subtotal',
                               readonly=True, store=True)
    product_uom_qty = fields.Float(string='Quantity',
                                   digits=dp.get_precision('Product Unit of Measure'),
                                   required=True,
                                   default=1.0)

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            #TODO change pricelist for partner
            pricelist_id = self.env['ir.default'].sudo().get(
                'res.config.settings', 'parity_pricelist_id')
            prod = self.product_id.with_context(
                lang=self.folio_wizard_id.partner_id.lang,
                partner=self.folio_wizard_id.partner_id.id,
                quantity=1,
                date=fields.Datetime.now(),
                pricelist=pricelist_id,
                uom=self.product_id.uom_id.id)
            self.price_unit = prod.price

    @api.depends('price_unit', 'product_uom_qty', 'discount')
    def _compute_amount(self):
        for ser in self:
            total = (ser.price_unit * ser.product_uom_qty)
            ser.price_total = total - (total * ser.discount) * 0.01
