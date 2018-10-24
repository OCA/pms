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
    def _get_default_node_id(self):
        return self._context.get('node_id') or None

    @api.model
    def _get_default_checkin(self):
        pass

    @api.model
    def _get_default_checkout(self):
        pass

    node_id = fields.Many2one('project.project', 'Hotel', required=True,
                              default=_get_default_node_id)

    partner_id = fields.Many2one('res.partner', string="Customer", required=True)

    checkin = fields.Date('Check In', required=True,
                          default=_get_default_checkin)
    checkout = fields.Date('Check Out', required=True,
                           default=_get_default_checkout)

    room_type_wizard_ids = fields.One2many('node.room.type.wizard', 'node_reservation_wizard_id',
                                           string="Room Types")
    price_total = fields.Float(string='Total Price', default=250.0)

    @api.onchange('node_id')
    def _onchange_node_id(self):
        # self.ensure_one()
        if self.node_id:
            _logger.info('onchange_node_id(self): %s', self)
            try:
                noderpc = odoorpc.ODOO(self.node_id.odoo_host, self.node_id.odoo_protocol, self.node_id.odoo_port)
                noderpc.login(self.node_id.odoo_db, self.node_id.odoo_user, self.node_id.odoo_password)

                today = fields.Date.context_today(self.with_context())

                # TODO check hotel timezone
                checkin = fields.Date.from_string(today).strftime(
                    DEFAULT_SERVER_DATE_FORMAT) if not self.checkin else fields.Date.from_string(self.checkin)

                checkout = (fields.Date.from_string(today) + timedelta(days=1)).strftime(
                    DEFAULT_SERVER_DATE_FORMAT) if not self.checkout else fields.Date.from_string(self.checkout)

                free_room_ids = noderpc.env['hotel.room.type'].check_availability_room_ids(checkin, checkout)

                room_type_availability = {}
                for room_type in self.node_id.room_type_ids:
                    availability_real = noderpc.env['hotel.room'].search_count([
                        ('id', 'in', free_room_ids),
                        ('room_type_id', '=', room_type.remote_room_type_id),
                    ])
                    availability_plan = noderpc.env['hotel.room.type.availability'].search_read([
                        ('date', '>=', checkin),
                        ('date', '<', checkout),
                        ('room_type_id', '=', room_type.remote_room_type_id),

                    ], ['avail']) or float('inf')

                    if isinstance(availability_plan, list):
                        availability_plan = min([r['avail'] for r in availability_plan])

                    room_type_availability[room_type.id] = min(
                        availability_real, availability_plan)

                cmds = self.node_id.room_type_ids.mapped(lambda room_type_id: (0, False, {
                    'room_type_id': room_type_id.id,
                    'checkin': checkin,
                    'checkout': checkout,
                    'room_type_availability': room_type_availability[room_type_id.id],
                    'node_reservation_wizard_id': self.id,

                }))
                self.update({
                    'checkin': checkin,
                    'checkout': checkout,
                    'room_type_wizard_ids': cmds,
                })
                noderpc.logout()
            except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
                raise ValidationError(err)

    @api.onchange('checkin', 'checkout')
    def _onchange_dates(self):
        _logger.info('_onchange_dates(self): %s', self)

        today = fields.Date.context_today(self.with_context())

        # TODO check hotel timezone
        self.checkin = fields.Date.from_string(today).strftime(
            DEFAULT_SERVER_DATE_FORMAT) if not self.checkin else fields.Date.from_string(self.checkin)

        self.checkout = (fields.Date.from_string(today) + timedelta(days=1)).strftime(
            DEFAULT_SERVER_DATE_FORMAT) if not self.checkout else fields.Date.from_string(self.checkout)

        if fields.Date.from_string(self.checkin) >= fields.Date.from_string(self.checkout):
            self.checkout = (fields.Date.from_string(self.checkin) + timedelta(days=1)).strftime(
            DEFAULT_SERVER_DATE_FORMAT)

        for room_type in self.room_type_wizard_ids:
            room_type.checkin = self.checkin
            room_type.checkout = self.checkout

    @api.multi
    def create_node_reservation(self):
        try:
            noderpc = odoorpc.ODOO(self.node_id.odoo_host, self.node_id.odoo_protocol, self.node_id.odoo_port)
            noderpc.login(self.node_id.odoo_db, self.node_id.odoo_user, self.node_id.odoo_password)

            # prepare required fields for hotel folio
            remote_partner_id = noderpc.env['res.partner'].search([('email','=',self.partner_id.email)]).pop()
            vals = {
                'partner_id': remote_partner_id,
                'name': 'New',
            }
            # prepare hotel folio room_lines
            room_lines = []
            for line in self.room_type_wizard_ids:
                if line.room_qty > 0:
                    vals_reservation_lines = {
                        'partner_id': remote_partner_id,
                        'room_type_id': line.room_type_id.remote_room_type_id,
                    }
                    reservation_line_ids = noderpc.env['hotel.reservation'].prepare_reservation_lines(
                        line.checkin,
                        (fields.Date.from_string(line.checkout) - fields.Date.from_string(line.checkin)).days,
                        vals_reservation_lines
                    ) # [[5, 0, 0], ¿?

                    room_lines.append((0, False, {
                        'name': 'Descripcion del pedido de venta',
                        'room_type_id': line.room_type_id.remote_room_type_id,
                        'checkin': line.checkin,
                        'checkout': line.checkout,
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

    def _default_checkin(self):
        today = fields.Date.context_today(self.with_context())
        return self.node_reservation_wizard_id.checkin or \
               fields.Date.from_string(today).strftime(DEFAULT_SERVER_DATE_FORMAT)

    def _default_checkout(self):
        today = fields.Date.context_today(self.with_context())
        return self.node_reservation_wizard_id.checkin or \
               (fields.Date.from_string(today) + timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT)

    node_reservation_wizard_id = fields.Many2one('hotel.node.reservation.wizard')
    node_id = fields.Many2one(related='node_reservation_wizard_id.node_id')

    room_type_id = fields.Many2one('hotel.node.room.type', 'Rooms Type')
    room_type_name = fields.Char('Name', related='room_type_id.name')
    room_type_availability = fields.Integer('Availability') #, compute="_compute_room_type_availability")
    room_qty = fields.Integer('Quantity', default=0)

    checkin = fields.Date('Check In', required=True, default=_default_checkin)
    checkout = fields.Date('Check Out', required=True, default=_default_checkout)

    price_unit = fields.Float(string='Room Price', required=True, default=0.0)
    discount = fields.Float(string='Discount (%)', default=0.0)
    price_total = fields.Float(string='Total Price', compute="_compute_price_total")

    # compute and search fields, in the same order that fields declaration
    @api.onchange('checkin','checkout')
    def _onchange_dates(self):
        _logger.info('_onchange_dates for room type %s', self.room_type_id)
        wdb.set_trace()
        # if self.checkin and self.checkout:

         # Conectar con nodo para traer dispo(availability) y precio por habitación(price_unit)
         # availability: search de hotel.room.type.availability filtrando por room_type y date y escogiendo el min avail en el rango
         # preci_unit y json_days: usando prepare_reservation_lines

    @api.depends('room_qty', 'price_unit', 'discount', 'checkin', 'checkout')
    def _compute_price_total(self):
        _logger.info('_compute_price_total')
        for record in self:
            record.price_total = (record.room_qty * record.price_unit) * (1.0 - record.discount * 0.01)
         # Unidades x precio unidad (el precio de unidad ya incluye el conjunto de días)

