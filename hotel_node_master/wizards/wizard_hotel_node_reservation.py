# Copyright 2018  Pablo Q. Barriuso
# Copyright 2018  Alexandre Díaz
# Copyright 2018  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import wdb
import logging
import urllib.error
import odoorpc.odoo
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT)

_logger = logging.getLogger(__name__)


class HotelNodeReservationWizard(models.TransientModel):
    # TODO Rename to node.engine.reservation.wizard
    _name = "hotel.node.reservation.wizard"
    _description = "Hotel Node Reservation Wizard"

    @api.model
    def _default_node_id(self):
        return self._context.get('node_id') or None

    @api.model
    def _default_checkin(self):
        today = fields.Date.context_today(self.with_context())
        return fields.Date.from_string(today).strftime(DEFAULT_SERVER_DATE_FORMAT)

    @api.model
    def _default_checkout(self):
        today = fields.Date.context_today(self.with_context())
        return (fields.Date.from_string(today) + timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT)

    node_id = fields.Many2one('project.project', 'Hotel', required=True, default=_default_node_id)
    partner_id = fields.Many2one('res.partner', string="Customer", required=True)
    room_type_wizard_ids = fields.One2many('node.room.type.wizard', 'node_reservation_wizard_id',
                                           string="Room Types")
    price_total = fields.Float(string='Total Price', compute='_compute_price_total', store=True)

    # FIXED @constrains parameter 'room_type_wizard_ids.room_qty' is not a field name
    # @api.constrains('room_type_wizard_ids')
    # def _check_room_type_wizard_total_qty(self):
    #     for rec in self:
    #         total_qty = 0
    #         for rec_room_type in rec.room_type_wizard_ids:
    #             total_qty += rec_room_type.room_qty
    #
    #         if total_qty == 0:
    #             msg = _("It is not possible to create the reservation.") + " " + \
    #                   _("Maybe you forgot adding the quantity to at least one type of room?.")
    #             raise ValidationError(msg)

    @api.depends('room_type_wizard_ids.price_total')
    def _compute_price_total(self):
        for rec in self:
            _logger.info('_compute_price_total for wizard %s', rec.id)
            rec.price_total = 0.0
            for rec_room_type in rec.room_type_wizard_ids:
                rec.price_total += rec_room_type.price_total

    @api.onchange('node_id')
    def _onchange_node_id(self):
        if self.node_id:
            _logger.info('_onchange_node_id(self): %s', self)
            # TODO Save your credentials (session)
            _logger.info('_compute_room_types for node %s', self.node_id)
            cmds = self.node_id.room_type_ids.mapped(lambda room_type_id: (0, False, {
                'node_id': self.node_id.id,
                'room_type_id': room_type_id.id,
                'checkin': self._default_checkin(),
                'checkout': self._default_checkout(),
            }))
            self.room_type_wizard_ids = cmds

    @api.model
    def create(self, vals):
        # TODO review node.room.type.wizard @api.constrains('room_qty')
        from pprint import pprint
        try:
            node = self.env["project.project"].browse(vals['node_id'])

            noderpc = odoorpc.ODOO(node.odoo_host, node.odoo_protocol, node.odoo_port)
            noderpc.login(node.odoo_db, node.odoo_user, node.odoo_password)

            # prepare required fields for hotel.folio
            remote_vals = {}
            partner = self.env["res.partner"].browse(vals['partner_id'])
            remote_partner_id = noderpc.env['res.partner'].search([('email', '=', partner.email)]).pop()
            # TODO create partner if does not exist in remote node
            remote_vals.update({
                'partner_id': remote_partner_id,
            })

            # prepare hotel.folio.room_lines
            room_lines = []
            for cmds in vals['room_type_wizard_ids']:
                # cmds is a list of triples: [0, 'virtual_1008', {'checkin': '2018-11-05', ...
                room_type_wizard_values = cmds[2]
                remote_room_type_id = self.env['hotel.node.room.type'].search([
                    ('id', '=', room_type_wizard_values['room_type_id'])
                ]).remote_room_type_id
                # prepare room_lines a number of times `room_qty` times
                for room in range(room_type_wizard_values['room_qty']):
                    # prepare hotel.reservation.reservation_line_ids
                    reservation_line_cmds = []
                    for room_type_line_cmds in room_type_wizard_values['room_type_line_ids']:
                        reservation_line = room_type_line_cmds[2]
                        reservation_line_cmds.append((0, False, {
                            'date': reservation_line['date'],
                            'price': reservation_line['price'],
                        }))
                    # add discount ¿?
                    room_lines.append((0, False, {
                        'room_type_id': remote_room_type_id,
                        'checkin': room_type_wizard_values['checkin'],
                        'checkout': room_type_wizard_values['checkout'],
                        'reservation_line_ids': reservation_line_cmds,
                    }))
            remote_vals.update({'room_lines': room_lines})

            pprint(remote_vals)
            # if total_qty == 0:
            #     msg = _("It is not possible to create the reservation.") + " " + \
            #           _("Maybe you forgot adding the quantity to at least one type of room?.")
            #     raise ValidationError(msg)
            folio_id = noderpc.env['hotel.folio'].create(remote_vals)
            _logger.info('User #%s created a remote hotel.folio with ID: [%s]',
                         self._context.get('uid'), folio_id)

            noderpc.logout()

        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            _logger.error(err)
            raise ValidationError(err)
        else:
            return super().create(vals)

    @api.multi
    def create_node_reservation(self):
        _logger.info('# TODO: return a wizard and preview the reservation')
        # self.ensure_one()
        # # NOTE This function is executed __after__ create(self, vals) where _compute_restrictions are executed again
        # try:
        #     noderpc = odoorpc.ODOO(self.node_id.odoo_host, self.node_id.odoo_protocol, self.node_id.odoo_port)
        #     noderpc.login(self.node_id.odoo_db, self.node_id.odoo_user, self.node_id.odoo_password)
        #
        #     # prepare required fields for hotel folio
        #     remote_partner_id = noderpc.env['res.partner'].search([('email', '=', self.partner_id.email)]).pop()
        #     vals = {
        #         'partner_id': remote_partner_id,
        #     }
        #     # prepare hotel folio room_lines
        #     room_lines = []
        #     for rec in self.room_type_wizard_ids:
        #         for x in range(rec.room_qty):
        #             # prepare hotel reservation lines with details by day
        #             reservation_line_cmds = rec.room_type_line_ids.mapped(lambda reservation_line: (0, False, {
        #                 'date': reservation_line.date,
        #                 'price': reservation_line.price,
        #             }))
        #             # add discount
        #             room_lines.append((0, False, {
        #                 'room_type_id': rec.room_type_id.remote_room_type_id,
        #                 'checkin': rec.checkin,
        #                 'checkout': rec.checkout,
        #                 'reservation_line_ids': reservation_line_cmds,
        #             }))
        #     vals.update({'room_lines': room_lines})
        #
        #     from pprint import pprint
        #     pprint(vals)
        #
        #     folio_id = noderpc.env['hotel.folio'].create(vals)
        #     _logger.info('User #%s created a hotel.folio with ID: [%s]',
        #                  self._context.get('uid'), folio_id)
        #
        #     noderpc.logout()
        # except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
        #     raise ValidationError(err)

    @api.multi
    def _open_wizard_action_search(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }


class NodeRoomTypeWizard(models.TransientModel):
    _name = "node.room.type.wizard"
    _description = "Node Room Type Wizard"

    @api.model
    def _default_node_id(self):
        return self._context.get('node_id') or None

    @api.model
    def _default_checkin(self):
        today = fields.Date.context_today(self.with_context())
        return fields.Date.from_string(today).strftime(DEFAULT_SERVER_DATE_FORMAT)

    @api.model
    def _default_checkout(self):
        today = fields.Date.context_today(self.with_context())
        return (fields.Date.from_string(today) + timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT)

    node_reservation_wizard_id = fields.Many2one('hotel.node.reservation.wizard',
                                                 ondelete = 'cascade', required = True)
    node_id = fields.Many2one('project.project', 'Hotel', default=_default_node_id, required=True)

    room_type_id = fields.Many2one('hotel.node.room.type', 'Rooms Type')
    room_type_availability = fields.Integer('Availability', compute="_compute_restrictions", readonly=True, store=True)
    room_qty = fields.Integer('Quantity', default=0)
    room_type_line_ids = fields.One2many('node.room.type.line.wizard', 'node_room_type_line_wizard_id',
                                         string="Room type detail per day")

    checkin = fields.Date('Check In', default=_default_checkin, required=True)
    checkout = fields.Date('Check Out', default=_default_checkout, required=True)
    nights = fields.Integer('Nights', compute='_compute_nights', readonly=True)

    min_stay = fields.Integer('Min. Days', compute="_compute_restrictions", readonly=True, store=True)
    price_unit = fields.Float(string='Room Price', compute="_compute_restrictions", readonly=True, store=True)
    discount = fields.Float(string='Discount (%)', default=0.0)
    price_total = fields.Float(string='Total Price', compute='_compute_price_total', readonly=True, store=True)

    @api.constrains('room_qty')
    def _check_room_qty(self):
        # At least one model cache has been invalidated, signaling through the database.
        for rec in self:
            if (rec.room_type_availability < rec.room_qty) or (rec.room_qty > 0 and rec.nights < rec.min_stay):
                msg = _("At least one room type has not availability or does not meet restrictions.") + " " + \
                      _("Please, review room type %s between %s and %s.") % (rec.room_type_id.name, rec.checkin, rec.checkout)
                _logger.warning(msg)
                raise ValidationError(msg)

    @api.depends('room_qty', 'price_unit', 'discount')
    def _compute_price_total(self):
        for rec in self:
            _logger.info('_compute_price_total for room type %s', rec.room_type_id)
            rec.price_total = (rec.room_qty * rec.price_unit) * (1.0 - rec.discount * 0.01)

    @api.depends('checkin', 'checkout')
    def _compute_nights(self):
        for rec in self:
            rec.nights = (fields.Date.from_string(rec.checkout) - fields.Date.from_string(rec.checkin)).days

    @api.depends('checkin', 'checkout')
    def _compute_restrictions(self):
        for rec in self:
            if rec.checkin and rec.checkout:
                try:
                    # TODO Load your credentials (session) ... should be faster?
                    noderpc = odoorpc.ODOO(rec.node_id.odoo_host, rec.node_id.odoo_protocol, rec.node_id.odoo_port)
                    noderpc.login(rec.node_id.odoo_db, rec.node_id.odoo_user, rec.node_id.odoo_password)

                    _logger.info('_compute_restrictions [availability] for room type %s', rec.room_type_id)
                    rec.room_type_availability = noderpc.env['hotel.room.type'].get_room_type_availability(
                            rec.checkin,
                            rec.checkout,
                            rec.room_type_id.remote_room_type_id)

                    _logger.info('_compute_restrictions [price_unit] for room type %s', rec.room_type_id)
                    rec.room_type_line_ids = noderpc.env['hotel.room.type'].get_room_type_price_unit(
                            rec.checkin,
                            rec.checkout,
                            rec.room_type_id.remote_room_type_id)
                    # cmds = []
                    # for x in range(rec.nights):
                    #     cmds.append((0, False, {
                    #         'date': (fields.Date.from_string(rec.checkin) + timedelta(days=x)).strftime(
                    #             DEFAULT_SERVER_DATE_FORMAT),
                    #         'price': 11.50,
                    #     }))
                    # from pprint import pprint
                    # pprint(cmds)
                    # rec.room_type_line_ids = cmds
                    rec.price_unit = sum(rec.room_type_line_ids.mapped('price'))

                    _logger.info('_compute_restrictions [min days] for room type %s', rec.room_type_id)
                    rec.min_stay = noderpc.env['hotel.room.type'].get_room_type_restrictions(
                        rec.checkin,
                        rec.checkout,
                        rec.room_type_id.remote_room_type_id)

                    noderpc.logout()
                except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
                    raise ValidationError(err)

    @api.onchange('room_qty')
    def _onchange_room_qty(self):
        if self.room_type_availability < self.room_qty:
            msg = _("Please, review room type %s between %s and %s.") % (self.room_type_id.name, self.checkin, self.checkout)
            return {
                'warning': {
                    'title': 'Warning: Invalid room quantity',
                    'message': msg,
                }
            }

    @api.onchange('checkin', 'checkout')
    def _onchange_dates(self):
        _logger.info('_onchange_dates for room type: %s', self.room_type_id)
        if not self.checkin:
            self.checkin = self._default_checkin()
        if not self.checkout:
            self.checkout = self._default_checkout()

        if fields.Date.from_string(self.checkin) >= fields.Date.from_string(self.checkout):
            self.checkout = (fields.Date.from_string(self.checkin) + timedelta(days=1)).strftime(
                DEFAULT_SERVER_DATE_FORMAT)


class NodeRoomTypeLineWizard(models.TransientModel):
    _name = "node.room.type.line.wizard"
    _description = "Node Room Type Detail per Day Wizard"

    node_room_type_line_wizard_id = fields.Many2one('node.room.type.wizard',
                                                    ondelete='cascade', required=True)
    date = fields.Date('Date')
    price = fields.Float('Price')


class NodeSearchWizard(models.TransientModel):
    _name = "node.search.wizard"
    _description = "Node Search Wizard"

    @api.model
    def _default_node_id(self):
        return self._context.get('node_id') or None

    node_id = fields.Many2one('project.project', 'Hotel', default=_default_node_id)
    node_folio_wizard_id = fields.Many2one('node.folio.wizard')
    folio = fields.Char('Folio Number')
    partner_id = fields.Many2one('res.partner', string="Customer")
    email = fields.Char('E-mail', related='partner_id.email')
    checkin = fields.Date('Check In')
    checkout = fields.Date('Check Out')

    @api.multi
    def search_node_reservation(self):
        self.ensure_one()
        try:
            noderpc = odoorpc.ODOO(self.node_id.odoo_host, self.node_id.odoo_protocol, self.node_id.odoo_port)
            noderpc.login(self.node_id.odoo_db, self.node_id.odoo_user, self.node_id.odoo_password)

            domain = []
            if self.folio:
                domain.append(('name', '=', 'F/' + self.folio))
            if self.partner_id:
                domain.append(('email', '=', self.email))
            if self.checkin:
                domain.append(('checkin', '=', self.checkin))

            folio_ids = noderpc.env['hotel.folio'].search(domain)

            if not folio_ids:
                raise UserError(_("No reservations found for [%s].") % domain)

            noderpc.logout()

            if len(folio_ids) > 1:
                # TODO Need to manage more than one folio
                return self._open_wizard_action_select(folio_ids)

            return self._open_wizard_action_edit(folio_ids.pop())

        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)

    @api.multi
    def _open_wizard_action_select(self, folio_ids):
        self.ensure_one()
        return {
            'name': _('Hotel Reservation Wizard Select'),
            'type': 'ir.actions.act_window',
            'res_model': 'node.folio.wizard',
            'view_id': self.env.ref('hotel_node_master.hotel_node_reservation_wizard_view_tree', False).id,
            'view_type': 'tree',
            'view_mode': 'tree',
        }

    @api.multi
    def _open_wizard_action_edit(self, folio_id):
        self.ensure_one()
        return {
            'name': _('Hotel Reservation Wizard Edit'),
            'type': 'ir.actions.act_window',
            'res_model': 'node.folio.wizard',
            'view_id': self.env.ref('hotel_node_master.hotel_node_reservation_wizard_view_edit_form', False).id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {'folio_id': folio_id},
        }


class NodeFolioWizard(models.TransientModel):
    _name = 'node.folio.wizard'

    @api.model
    def _default_node_id(self):
        return self._context.get('node_id') or None

    @api.model
    def _default_folio_id(self):
        return self._context.get('folio_id') or None

    node_id = fields.Many2one('project.project', 'Hotel', required=True, default=_default_node_id)
    folio_id = fields.Integer(required=True, default=_default_folio_id)
    folio_name = fields.Char('Folio Number', readonly=True)
    partner_id = fields.Many2one('res.partner', string="Customer", required=True)
    internal_comment = fields.Text(string='Internal Folio Notes')
    # For being used directly in the Folio views
    email = fields.Char('E-mail', related='partner_id.email')
    room_lines_wizard_ids = fields.One2many('node.reservation.wizard', 'node_folio_wizard_id')
    price_total = fields.Float(string='Total Price')

    @api.onchange('node_id')
    def _onchange_node_id(self):
        self.ensure_one()
        _logger.info('_onchange_node_id(self): %s', self)

        noderpc = odoorpc.ODOO(self.node_id.odoo_host, self.node_id.odoo_protocol, self.node_id.odoo_port)
        noderpc.login(self.node_id.odoo_db, self.node_id.odoo_user, self.node_id.odoo_password)

        folio = noderpc.env['hotel.folio'].browse(self.folio_id)

        self.folio_name = folio.name
        self.partner_id = self.env['res.partner'].search([('email', '=', folio.partner_id.email)])
        self.internal_comment = folio.internal_comment
        self.price_total = folio.amount_total

        cmds = []
        for reservation in folio.room_lines:
            cmds.append((0, False, {
                'node_folio_wizard_id': self.id,
                'room_type_id': self.env['hotel.node.room.type'].search([
                    ('node_id', '=', self.node_id.id),
                    ('remote_room_type_id', '=', reservation.room_type_id.id),
                    ]).id,
                'adults': reservation.adults,
                'children': reservation.children,
                'checkin': reservation.checkin,
                'checkout': reservation.checkout,
                'nights': reservation.nights,
                'state': reservation.state,
                'price_total': reservation.price_total,
            }))

        self.room_lines_wizard_ids = cmds

    @api.multi
    def update_node_reservation(self):
        self.ensure_one()
        try:
            raise UserError(_("Function under development."))
        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)


class NodeReservationWizard(models.TransientModel):
    _name = 'node.reservation.wizard'

    node_folio_wizard_id = fields.Many2one('node.folio.wizard')
    room_type_id = fields.Many2one('hotel.node.room.type', 'Rooms Type')
    room_type_name = fields.Char('Name', related='room_type_id.name')
    checkin = fields.Date('Check In', required=True)
    checkout = fields.Date('Check Out', required=True)
    nights = fields.Integer('Nights', compute="_compute_nights", readonly=True)

    adults = fields.Integer('Adults', size=64, default=1)
    children = fields.Integer('Children', size=64)

    state = fields.Selection([('draft', 'Pre-reservation'), ('confirm', 'Pending Entry'),
                              ('booking', 'On Board'), ('done', 'Out'),
                              ('cancelled', 'Cancelled')], 'State')
    price_total = fields.Float(string='Total Price', readonly=True)

    @api.depends('checkin', 'checkout')
    def _compute_nights(self):
        for rec in self:
            rec.nights = (fields.Date.from_string(rec.checkout) - fields.Date.from_string(rec.checkin)).days
