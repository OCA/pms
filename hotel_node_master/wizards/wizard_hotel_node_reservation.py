# Copyright 2018  Pablo Q. Barriuso
# Copyright 2018  Alexandre Díaz
# Copyright 2018  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from builtins import list

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

    @api.depends('room_type_wizard_ids.price_total')
    def _compute_price_total(self):
        _logger.info('_compute_price_total for wizard %s', self.id)
        price_total = 0.0
        for record in self.room_type_wizard_ids:
            price_total += record.price_total
        self.price_total = price_total

    @api.onchange('node_id')
    def _onchange_node_id(self):
        self.ensure_one()
        if self.node_id:
            _logger.info('_onchange_node_id(self): %s', self)
            # Save your credentials (session)

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

        try:
            noderpc = odoorpc.ODOO(self.node_id.odoo_host, self.node_id.odoo_protocol, self.node_id.odoo_port)
            noderpc.login(self.node_id.odoo_db, self.node_id.odoo_user, self.node_id.odoo_password)

            # free_room_ids = noderpc.env['hotel.room.type'].check_availability_room_ids(self.checkin, self.checkout)
            room_type_availability = {}
            # room_type_price_unit = {}
            for room_type in self.node_id.room_type_ids:
                room_type_availability[room_type.id] = \
                    noderpc.env['hotel.room.type'].get_room_type_availability(
                        self.checkin, self.checkout, room_type.remote_room_type_id)
                # availability_real = noderpc.env['hotel.room'].search_count([
                #     ('id', 'in', free_room_ids),
                #     ('room_type_id', '=', room_type.remote_room_type_id),
                # ])
                # availability_plan = noderpc.env['hotel.room.type.availability'].search_read([
                #     ('date', '>=', self.checkin),
                #     ('date', '<', self.checkout),
                #     ('room_type_id', '=', room_type.remote_room_type_id),
                #
                # ], ['avail']) or float('inf')
                #
                # if isinstance(availability_plan, list):
                #     availability_plan = min([r['avail'] for r in availability_plan])
                #
                # room_type_availability[room_type.id] = min(
                #     availability_real, availability_plan)

                # room_type_price_unit[room_type.id] = noderpc.env['hotel.room.type'].search_read([
                #     ('id', '=', room_type.remote_room_type_id),
                # ], ['list_price'])[0]['list_price']

            nights = (fields.Date.from_string(self.checkout) - fields.Date.from_string(self.checkin)).days

            cmds = self.node_id.room_type_ids.mapped(lambda room_type_id: (0, False, {
                'room_type_id': room_type_id.id,
                'checkin': self.checkin,
                'checkout': self.checkout,
                'nights': nights,
                'room_type_availability': room_type_availability[room_type_id.id],
                # 'price_unit': room_type_price_unit[room_type_id.id],
                'node_reservation_wizard_id': self.id,
            }))
            self.room_type_wizard_ids = cmds

            noderpc.logout()

        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)

    @api.multi
    def create_node_reservation(self):
        try:
            noderpc = odoorpc.ODOO(self.node_id.odoo_host, self.node_id.odoo_protocol, self.node_id.odoo_port)
            noderpc.login(self.node_id.odoo_db, self.node_id.odoo_user, self.node_id.odoo_password)

            # prepare required fields for hotel folio
            remote_partner_id = noderpc.env['res.partner'].search([('email','=',self.partner_id.email)]).pop()
            vals = {
                'partner_id': remote_partner_id,
            }
            # prepare hotel folio room_lines
            room_lines = []
            for room_type in self.room_type_wizard_ids:
                for x in range(room_type.room_qty):
                    vals_reservation_lines = {
                        'partner_id': remote_partner_id,
                        'room_type_id': room_type.room_type_id.remote_room_type_id,
                    }
                    # add discount
                    reservation_line_ids = noderpc.env['hotel.reservation'].prepare_reservation_lines(
                        room_type.checkin,
                        (fields.Date.from_string(room_type.checkout) - fields.Date.from_string(room_type.checkin)).days,
                        vals_reservation_lines
                    ) # [[5, 0, 0], ¿?

                    room_lines.append((0, False, {
                        'room_type_id': room_type.room_type_id.remote_room_type_id,
                        'checkin': room_type.checkin,
                        'checkout': room_type.checkout,
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
    room_type_availability = fields.Integer('Availability', readonly=True) #, compute="_compute_room_type_availability")
    room_qty = fields.Integer('Quantity', default=0)

    checkin = fields.Date('Check In', required=True)
    checkout = fields.Date('Check Out', required=True)
    nights = fields.Integer('Nights', readonly=True)
    min_stay = fields.Integer('Min. Days', compute="_compute_restrictions", readonly=True)

    price_unit = fields.Float(string='Room Price', required=True, default=0.0, readonly=True)
    discount = fields.Float(string='Discount (%)', default=0.0)
    price_total = fields.Float(string='Total Price', compute='_compute_price_total')

    @api.depends('room_qty', 'price_unit', 'discount')
    def _compute_price_total(self):
        for room_type in self:
            _logger.info('_compute_price_total for room type %s', room_type.room_type_id)
        # noderpc = odoorpc.ODOO(self.node_id.odoo_host, self.node_id.odoo_protocol, self.node_id.odoo_port)
        # noderpc.login(self.node_id.odoo_db, self.node_id.odoo_user, self.node_id.odoo_password)
        # self.price_unit = noderpc.env['hotel.room.type'].search_read([
        #     ('id', '=', self.room_type_id.remote_room_type_id),
        # ], ['list_price'])[0]['list_price']
        # noderpc.logout()

            room_type.price_total = (room_type.room_qty * room_type.price_unit * room_type.nights) * (1.0 - room_type.discount * 0.01)
        # Unidades x precio unidad (el precio de unidad ya incluye el conjunto de días)

    @api.depends('checkin', 'checkout')
    def _compute_restrictions(self):
        for room_type in self:
            _logger.info('_compute_restrictions for room type %s', room_type.room_type_id)

    @api.onchange('checkin', 'checkout')
    def _onchange_dates(self):
        _logger.info('_onchange_dates for room type %s', self.room_type_id)
        # recompute price unit
        self.checkin = self._default_checkin() \
            if not self.checkin else fields.Date.from_string(self.checkin)
        self.checkout = self._default_checkout() \
            if not self.checkout else fields.Date.from_string(self.checkout)
        if fields.Date.from_string(self.checkin) >= fields.Date.from_string(self.checkout):
            self.checkout = (fields.Date.from_string(self.checkin) + timedelta(days=1)).strftime(
                DEFAULT_SERVER_DATE_FORMAT)

        self.nights = (fields.Date.from_string(self.checkout) - fields.Date.from_string(self.checkin)).days

         # Conectar con nodo para traer dispo(availability) y precio por habitación(price_unit)
         # availability: search de hotel.room.type.availability filtrando por room_type y date y escogiendo el min avail en el rango
         # preci_unit y json_days: usando prepare_reservation_lines

