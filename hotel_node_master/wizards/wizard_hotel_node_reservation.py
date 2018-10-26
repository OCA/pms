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
from odoo.exceptions import ValidationError
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT)

_logger = logging.getLogger(__name__)


class HotelNodeReservationWizard(models.TransientModel):
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
    checkin = fields.Date('Check In', required=True, default=_default_checkin)
    checkout = fields.Date('Check Out', required=True, default=_default_checkout)
    room_type_wizard_ids = fields.One2many('node.room.type.wizard', 'node_reservation_wizard_id',
                                           string="Room Types")
    price_total = fields.Float(string='Total Price', compute='_compute_price_total')

    @api.constrains('room_type_wizard_ids')
    def _check_room_type_wizard_ids(self):
        """
        :raise: ValidationError
        """
        total_qty = 0
        for rec in self.room_type_wizard_ids:
            total_qty += rec.room_qty

        if total_qty == 0:
            msg = _("It is not possible to create the reservation.") + " " + \
                  _("Maybe you forgot adding the quantity to at least one type of room?.")
            raise ValidationError(msg)

    @api.depends('room_type_wizard_ids.price_total')
    def _compute_price_total(self):
        _logger.info('_compute_price_total for wizard %s', self.id)
        self.price_total = 0.0
        for rec in self.room_type_wizard_ids:
            self.price_total += rec.price_total

    @api.onchange('node_id')
    def _onchange_node_id(self):
        self.ensure_one()
        if self.node_id:
            _logger.info('_onchange_node_id(self): %s', self)
            # TODO Save your credentials (session)

    @api.onchange('checkin', 'checkout')
    def _onchange_dates(self):
        self.ensure_one()
        _logger.info('_onchange_dates(self): %s', self)

        # TODO check hotel timezone
        self.checkin = self._get_default_checkin() if not self.checkin \
            else fields.Date.from_string(self.checkin)
        self.checkout = self._get_default_checkout() if not self.checkout \
            else fields.Date.from_string(self.checkout)

        if fields.Date.from_string(self.checkin) >= fields.Date.from_string(self.checkout):
            self.checkout = (fields.Date.from_string(self.checkin) + timedelta(days=1)).strftime(
                DEFAULT_SERVER_DATE_FORMAT)

        cmds = self.node_id.room_type_ids.mapped(lambda room_type_id: (0, False, {
            'room_type_id': room_type_id.id,
            'checkin': self.checkin,
            'checkout': self.checkout,
            'nights': (fields.Date.from_string(self.checkout) - fields.Date.from_string(self.checkin)).days,
            # 'room_type_availability': room_type_availability[room_type_id.id],
            # 'price_unit': room_type_price_unit[room_type_id.id],
            'node_reservation_wizard_id': self.id,
        }))

        self.room_type_wizard_ids = cmds

    @api.multi
    def create_node_reservation(self):
        self.ensure_one()
        try:
            noderpc = odoorpc.ODOO(self.node_id.odoo_host, self.node_id.odoo_protocol, self.node_id.odoo_port)
            noderpc.login(self.node_id.odoo_db, self.node_id.odoo_user, self.node_id.odoo_password)

            # prepare required fields for hotel folio
            remote_partner_id = noderpc.env['res.partner'].search([('email', '=', self.partner_id.email)]).pop()
            vals = {
                'partner_id': remote_partner_id,
            }
            # prepare hotel folio room_lines
            room_lines = []
            for rec in self.room_type_wizard_ids:
                for x in range(rec.room_qty):
                    vals_reservation_lines = {
                        'partner_id': remote_partner_id,
                        'room_type_id': rec.room_type_id.remote_room_type_id,
                    }
                    # add discount
                    reservation_line_ids = noderpc.env['hotel.reservation'].prepare_reservation_lines(
                        rec.checkin,
                        (fields.Date.from_string(rec.checkout) - fields.Date.from_string(rec.checkin)).days,
                        vals_reservation_lines
                    )  # [[5, 0, 0], ¿?

                    room_lines.append((0, False, {
                        'room_type_id': rec.room_type_id.remote_room_type_id,
                        'checkin': rec.checkin,
                        'checkout': rec.checkout,
                        'reservation_line_ids': reservation_line_ids['reservation_line_ids'],
                    }))
            vals.update({'room_lines': room_lines})

            from pprint import pprint
            pprint(vals)

            folio_id = noderpc.env['hotel.folio'].create(vals)
            _logger.info('User #%s created a hotel.folio with ID: [%s]',
                         self._context.get('uid'), folio_id)

            noderpc.logout()
        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)


class NodeRoomTypeWizard(models.TransientModel):
    _name = "node.room.type.wizard"
    _description = "Node Room Type Wizard"

    node_reservation_wizard_id = fields.Many2one('hotel.node.reservation.wizard')
    node_id = fields.Many2one(related='node_reservation_wizard_id.node_id')

    room_type_id = fields.Many2one('hotel.node.room.type', 'Rooms Type')
    room_type_name = fields.Char('Name', related='room_type_id.name')
    room_type_availability = fields.Integer('Availability', compute="_compute_restrictions", readonly=True)
    room_qty = fields.Integer('Quantity', default=0)

    checkin = fields.Date('Check In', required=True)
    checkout = fields.Date('Check Out', required=True)
    nights = fields.Integer('Nights', compute="_compute_nights", readonly=True)
    min_stay = fields.Integer('Min. Days', compute="_compute_restrictions", readonly=True)
    # price_unit indicates Room Price x Nights
    price_unit = fields.Float(string='Room Price', compute="_compute_restrictions", readonly=True, store=True)
    discount = fields.Float(string='Discount (%)', default=0.0)
    price_total = fields.Float(string='Total Price', compute='_compute_price_total', readonly=True, store=True)

    @api.constrains('room_qty')
    def _check_room_qty(self):
        """
        :raise: ValidationError
        """
        total_qty = 0
        for rec in self:
            if (rec.room_type_availability < rec.room_qty) or (rec.room_qty > 0 and rec.nights < rec.min_stay):
                msg = _("At least one room type has not availability or does not meet restrictions.") + " " + \
                      _("Please, review room type %s between %s and %s.") % (rec.room_type_name, rec.checkin, rec.checkout)
                _logger.warning(msg)
                raise ValidationError(msg)
            total_qty += rec.room_qty

    @api.depends('room_qty', 'price_unit', 'discount')
    def _compute_price_total(self):
        for rec in self:
            _logger.info('_compute_price_total for room type %s', rec.room_type_id)
            rec.price_total = (rec.room_qty * rec.price_unit) * (1.0 - rec.discount * 0.01)
            # TODO rec.price unit trigger _compute_restriction ¿? store = True?

    @api.depends('checkin', 'checkout')
    def _compute_nights(self):
        for rec in self:
            rec.nights = (fields.Date.from_string(rec.checkout) - fields.Date.from_string(rec.checkin)).days

    @api.depends('checkin', 'checkout')
    def _compute_restrictions(self):
        for rec in self:
            try:
                # TODO Load your credentials (session) ... should be faster?
                noderpc = odoorpc.ODOO(rec.node_id.odoo_host, rec.node_id.odoo_protocol, rec.node_id.odoo_port)
                noderpc.login(rec.node_id.odoo_db, rec.node_id.odoo_user, rec.node_id.odoo_password)

                _logger.warning('_compute_restrictions [availability] for room type %s', rec.room_type_id)
                rec.room_type_availability = noderpc.env['hotel.room.type'].get_room_type_availability(
                        rec.checkin,
                        rec.checkout,
                        rec.room_type_id.remote_room_type_id)

                _logger.warning('_compute_restrictions [price_unit] for room type %s', rec.room_type_id)
                rec.price_unit = noderpc.env['hotel.room.type'].get_room_type_price_unit(
                        rec.checkin,
                        rec.checkout,
                        rec.room_type_id.remote_room_type_id)

                _logger.warning('_compute_restrictions [min days] for room type %s', rec.room_type_id)
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
            msg = _("Please, review room type %s between %s and %s.") % (self.room_type_name, self.checkin, self.checkout)
            return {
                'warning': {
                    'title': 'Warning: Invalid room quantity',
                    'message': msg,
                }
            }

    @api.onchange('checkin', 'checkout')
    def _onchange_dates(self):
        _logger.info('_onchange_dates for room type %s', self.room_type_id)

        self.checkin = self._default_checkin() \
            if not self.checkin else fields.Date.from_string(self.checkin)
        self.checkout = self._default_checkout() \
            if not self.checkout else fields.Date.from_string(self.checkout)

        if fields.Date.from_string(self.checkin) >= fields.Date.from_string(self.checkout):
            self.checkout = (fields.Date.from_string(self.checkin) + timedelta(days=1)).strftime(
                DEFAULT_SERVER_DATE_FORMAT)

