# Copyright 2018 Dario Lodeiros
# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import time
import logging
from datetime import datetime, timedelta
from openerp.exceptions import ValidationError
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
from openerp import models, fields, api, _
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
        if 'folio_id' in self._context:
            folio = self.env['hotel.folio'].search([
                ('id', '=', self._context['folio_id'])
            ])
        if folio and folio.room_lines:
            return folio.room_lines[0].checkin
        return fields.Date.today()

    @api.model
    def _get_default_checkout(self):
        folio = False
        if 'folio_id' in self._context:
            folio = self.env['hotel.folio'].search([
                ('id', '=', self._context['folio_id'])
            ])
        if folio and folio.room_lines:
            return folio.room_lines[0].checkout
        return fields.Date.today()

    @api.model
    def _get_default_channel_type(self):
        user = self.env['res.users'].browse(self.env.uid)
        if user.has_group('hotel.group_hotel_call'):
            return 'phone'

    partner_id = fields.Many2one('res.partner',string="Customer")
    checkin = fields.Date('Check In', required=True,
                              default=_get_default_checkin)
    checkout = fields.Date('Check Out', required=True,
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
                                            string="Room Types")
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
                occupied = self.env['hotel.reservation'].get_reservations(
                    line.checkin,
                    (fields.Date.from_string(line.checkout) - timedelta(days=1)).
                        strftime(DEFAULT_SERVER_DATE_FORMAT))
                rooms_occupied = occupied.mapped('room_id.id')
                free_rooms = self.env['hotel.room'].search([
                    ('id', 'not in', rooms_occupied),
                    ('room_type_id.id', '=', line.room_type_id.id)
                ], order='sequence', limit=line.rooms_num)
                room_ids = free_rooms.mapped('id')
                room_list = self.env['hotel.room'].search([
                    ('id', 'in', room_ids)
                ])
                checkin_dt = fields.Date.from_string(line.checkin)
                checkout_dt = fields.Date.from_string(line.checkout)
                nights = abs((checkout_dt - checkin_dt).days)
                for room in room_list:
                    pricelist_id = self.env['ir.default'].sudo().get(
                        'res.config.settings', 'default_pricelist_id')
                    if pricelist_id:
                        pricelist_id = int(pricelist_id)
                    res_price = 0
                    for i in range(0, nights):
                        ndate = checkin_dt + timedelta(days=i)
                        ndate_str = ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)
                        prod = line.room_type_id.product_id.with_context(
                            lang=self.partner_id.lang,
                            partner=self.partner_id.id,
                            quantity=1,
                            date=ndate_str,
                            pricelist=pricelist_id,
                            uom=room.room_type_id.product_id.uom_id.id)
                        res_price += prod.price
                    adults = self.env['hotel.room'].search([
                        ('id', '=', room.id)
                    ]).capacity
                    res_price = res_price - (res_price * line.discount)/100
                    total += res_price
                    cmds.append((0, False, {
                        'checkin': line.checkin,
                        'checkout': line.checkout,
                        'discount': line.discount,
                        'room_id': room.id,
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
        tz_hotel = self.env['ir.default'].sudo().get(
                'res.config.settings', 'tz_hotel')
        today = fields.Date.context_today(self.with_context(tz=tz_hotel))
        checkin_dt = fields.Date.from_string(today) if not self.checkin else fields.Date.from_string(self.checkin)
        checkout_dt = fields.Date.from_string(today) if not self.checkout else fields.Date.from_string(self.checkout)
        if checkin_dt >= checkout_dt:
            checkout_dt = checkin_dt + timedelta(days=1)

        checkin_str = checkin_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        checkout_str = checkout_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)

        room_type_ids = self.env['hotel.room.type'].search([])
        cmds = room_type_ids.mapped(lambda x: (0, False, {
            'room_type_id': x.id,
            'folio_wizard_id': self.id,
            'checkin': checkin_str,
            'checkout': checkout_str,
        }))
        self.update({
            'checkin': checkin_str,
            'checkout': checkout_str,
            'room_type_wizard_ids': cmds,
        })
        for room_type in self.room_type_wizard_ids:
            room_type.update_price()

    @api.depends('room_type_wizard_ids', 'reservation_wizard_ids', 'service_wizard_ids')
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
        if self.autoassign:
            self.create_reservations()
        for line in self.reservation_wizard_ids:
            reservations.append((0, False, {
                'room_id': line.room_id.id,
                'adults': line.adults,
                'children': line.children,
                'checkin': line.checkin,
                'checkout': line.checkout,
                'discount': line.discount,
                'room_type_id': line.room_type_id.id,
                'to_read': line.to_read,
                'to_assign': line.to_assign,
            }))
        for line in self.service_wizard_ids:
            services.append((0, False, {
                'product_id': line.product_id.id,
                'discount': line.discount,
                'price_unit': line.price_unit,
                'product_uom_qty': line.product_uom_qty,
            }))
        if not self.reservation_wizard_ids:
            raise ValidationError(_('We cant create avoid folio'))
        vals = {
            'partner_id': self.partner_id.id,
            'channel_type': self.channel_type,
            'room_lines': reservations,
            'service_lines': services,
        }
        newfol = self.env['hotel.folio'].create(vals)
        if self.confirm:
            newfol.room_lines.confirm()
        action = self.env.ref('hotel.open_hotel_folio1_form_tree_all').read()[0]
        if newfol:
            action['views'] = [(self.env.ref('hotel.hotel_folio_view_form').id, 'form')]
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
                                   string="Rooms Type")
    rooms_num = fields.Integer('Number of Rooms')
    max_rooms = fields.Integer('Max', compute="_compute_max")
    price = fields.Float(string='Price by Room')
    total_price = fields.Float(string='Total Price')
    folio_wizard_id = fields.Many2one('hotel.folio.wizard')
    amount_reservation = fields.Float(string='Total', readonly=True)
    discount = fields.Float('discount')
    min_stay = fields.Integer('Min. Days', compute="_compute_max")
    checkin = fields.Date('Check In', required=True,
                              default=_get_default_checkin)
    checkout = fields.Date('Check Out', required=True,
                               default=_get_default_checkout)
    can_confirm = fields.Boolean(compute="_can_confirm")

    @api.multi
    def _can_confirm(self):
        for record in self:
            date_start = fields.Date.from_string(record.checkin)
            date_end = fields.Date.from_string(record.checkout)
            date_diff = abs((date_end - date_start).days)
            record.can_confirm = record.max_rooms > 0 and record.min_stay <= date_diff

    def _compute_max(self):
        for res in self:
            user = self.env['res.users'].browse(self.env.uid)
            date_start = fields.Date.from_string(res.checkin)
            date_end = fields.Date.from_string(res.checkout)
            date_diff = abs((date_end - date_start).days)
            minstay_restrictions = self.env['hotel.room.type.restriction.item'].search([
                ('room_type_id', '=', res.room_type_id.id),
            ])
            avail_restrictions = self.env['hotel.room.type.availability'].search([
                ('room_type_id', '=', res.room_type_id.id)
            ])
            real_max = len(res.room_type_id.check_availability_room_type(
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


            if 100000 > avail > 0:
                res.max_rooms = avail
            else:
                res.max_rooms = 0
            if min_stay > 0:
                res.min_stay = min_stay

    @api.onchange('rooms_num', 'discount', 'price', 'room_type_id', 'checkin', 'checkout')
    def update_price(self):
        for record in self:
            if record.rooms_num > record.max_rooms:
                raise ValidationError(_("There are not enough rooms!"))
            checkin = record.checkin or record.folio_wizard_id.checkin
            checkout = record.checkout or record.folio_wizard_id.checkout
            chkin_utc_dt = fields.Date.from_string(checkin)
            chkout_utc_dt = fields.Date.from_string(checkout)
            if chkin_utc_dt >= chkout_utc_dt:
                chkout_utc_dt = chkin_utc_dt + timedelta(days=1)
            nights = abs((chkout_utc_dt - chkin_utc_dt).days)

            pricelist_id = self.env['ir.default'].sudo().get(
                'res.config.settings', 'default_pricelist_id')
            if pricelist_id:
                pricelist_id = int(pricelist_id)

            res_price = 0
            for i in range(0, nights):
                ndate = chkin_utc_dt + timedelta(days=i)
                ndate_str = ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)
                product = record.room_type_id.product_id.with_context(
                    lang=record.folio_wizard_id.partner_id.lang,
                    partner=record.folio_wizard_id.partner_id.id,
                    quantity=1,
                    date=ndate_str,
                    pricelist=pricelist_id,
                    uom=record.room_type_id.product_id.uom_id.id)
                res_price += self.env['account.tax']._fix_tax_included_price_company(
                    product.price, product.taxes_id, product.taxes_id, self.env.user.company_id)

            price = res_price - ((res_price * record.discount) * 0.01)
            total_price = record.rooms_num * price
            vals = {
                'checkin': checkin,
                'checkout': checkout,
                'price': price,
                'total_price': total_price,
                'amount_reservation': total_price,
            }
            _logger.info("NEW VUELTA ________________")
            _logger.info(record.room_type_id.name)
            _logger.info(vals)
            record.update(vals)


class ReservationWizard(models.TransientModel):
    _name = 'hotel.reservation.wizard'
    _rec_name = 'room_id'

    room_id = fields.Many2one('hotel.room',
                              string="Room")
    folio_wizard_id = fields.Many2one('hotel.folio.wizard')
    adults = fields.Integer('Adults',
                            help='List of adults there in guest list. ')
    children = fields.Integer('Children',
                              help='Number of children there in guest list.')
    checkin = fields.Date('Check In', required=True)
    checkout = fields.Date('Check Out', required=True)
    room_type_id = fields.Many2one('hotel.room.type',
                                   string='Room Type',
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
    @api.onchange('room_id')
    def onchange_room_id(self):
        for line in self:
            if line.checkin and line.checkout:
                if line.adults == 0:
                    line.adults = line.room_id.capacity
                line.room_type_id = line.room_id.room_type_id.id
                checkout_dt = fields.Date.from_string(line.checkout)
                checkout_dt -= timedelta(days=1)
                occupied = self.env['hotel.reservation'].get_reservations(
                    line.checkin,
                    checkout_dt.strftime(DEFAULT_SERVER_DATE_FORMAT))
                rooms_occupied = occupied.mapped('room_id.id')
                if line.room_id.id in rooms_occupied:
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

            start_date_utc_dt = fields.Date.from_string(line.checkin)
            end_date_utc_dt = fields.Date.from_string(line.checkout)

            if line.room_type_id:
                pricelist_id = self.env['ir.default'].sudo().get(
                    'res.config.settings', 'default_pricelist_id')
                if pricelist_id:
                    pricelist_id = int(pricelist_id)
                nights = abs((end_date_utc_dt - start_date_utc_dt).days)
                res_price = 0
                for i in range(0, nights):
                    ndate = start_date_utc_dt + timedelta(days=i)
                    ndate_str = ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    product = line.room_type_id.product_id.with_context(
                        lang=self.partner_id.lang,
                        partner=self.partner_id.id,
                        quantity=1,
                        date=ndate_str,
                        pricelist=pricelist_id,
                        uom=line.room_type_id.product_id.uom_id.id)
                    res_price += self.env['account.tax']._fix_tax_included_price_company(
                        product.price, product.taxes_id, product.taxes_id, self.env.user.company_id)
                res_price = res_price - (res_price * self.discount) * 0.01
                line.amount_reservation = res_price
                line.price = res_price
            end_date_utc_dt -= timedelta(days=1)
            occupied = self.env['hotel.reservation'].get_reservations(
                line.checkin,
                end_date_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT))
            rooms_occupied = occupied.mapped('room_id.id')
            domain_rooms = [('id', 'not in', rooms_occupied)]
            return {'domain': {'room_id': domain_rooms}}


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
    reservation_wizard_ids = fields.Many2many('hotel.reservation.wizard', 'Rooms')
    product_uom_qty = fields.Float(string='Quantity',
                                   digits=dp.get_precision('Product Unit of Measure'),
                                   required=True,
                                   default=1.0)

    @api.onchange('product_id', 'reservation_wizard_ids')
    def onchange_product_id(self):
        if self.product_id:
            vals = {}
            qty = 0
            vals['product_uom_qty'] = 1.0
            service_obj = self.env['hotel.service']
            if self.product_id.per_day:
                product = self.product_id
                for room in self.reservation_wizard_ids:
                    lines = {}
                    lines.update(service_obj.prepare_service_lines(
                            dfrom=room.checkin,
                            days=room.nights,
                            per_person=product.per_person,
                            persons=room.adults))
                    qty += lines.get('service_line_ids')[1][2]['day_qty']
                    if self.product_id.daily_limit > 0:
                        limit = self.product_id.daily_limit
                        for day in self.service_line_ids:
                            out_qty = sum(self.env['hotel.service.line'].search([
                                ('product_id', '=', self.product_id.id),
                                ('date', '=', self.date),
                                ('service_id', '!=', self.product_id.id)
                                ]).mapped('day_qty'))
                            if limit < out_qty + self.day_qty:
                                raise ValidationError(
                                _("%s limit exceeded for %s")% (self.service_id.product_id.name,
                                                                self.date))
                    vals['product_uom_qty'] = qty
            """
            Description and warnings
            """
            product = self.product_id.with_context(
                lang=self.folio_wizard_id.partner_id.lang,
                partner=self.folio_wizard_id.partner_id.id
            )
            title = False
            message = False
            warning = {}
            if product.sale_line_warn != 'no-message':
                title = _("Warning for %s") % product.name
                message = product.sale_line_warn_msg
                warning['title'] = title
                warning['message'] = message
                result = {'warning': warning}
                if product.sale_line_warn == 'block':
                    self.product_id = False
                    return result
            """
            Compute tax and price unit
            """
            #REVIEW: self._compute_tax_ids()
            # TODO change pricelist for partner
            pricelist_id = self.env['ir.default'].sudo().get(
                'res.config.settings', 'default_pricelist_id')
            product = self.product_id.with_context(
                lang=self.folio_wizard_id.partner_id.lang,
                partner=self.folio_wizard_id.partner_id.id,
                quantity=1,
                date=fields.Datetime.now(),
                pricelist=pricelist_id,
                uom=product.uom_id.id)
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(
                product.price, product.taxes_id, product.taxes_id, self.env.user.company_id)
            import wdb; wdb.set_trace()
            self.update(vals)

    @api.depends('price_unit', 'product_uom_qty', 'discount')
    def _compute_amount(self):
        for ser in self:
            total = (ser.price_unit * ser.product_uom_qty)
            ser.price_total = total - (total * ser.discount) * 0.01
