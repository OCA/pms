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
    def _get_default_checkin(self):
        pass

    @api.model
    def _get_default_checkout(self):
        pass

    node_id = fields.Many2one('project.project', 'Hotel', required=True)

    partner_id = fields.Many2one('res.partner', string="Customer", required=True)

    checkin = fields.Date('Check In', required=True,
                          default=_get_default_checkin)
    checkout = fields.Date('Check Out', required=True,
                           default=_get_default_checkout)

    room_type_wizard_ids = fields.Many2many('node.room.type.wizard',
                                            string="Room Types")

    @api.onchange('node_id')
    def onchange_node_id(self):
        self.ensure_one()
        if self.node_id:
            _logger.info('onchange_node_id(self): %s', self)
            try:
                noderpc = odoorpc.ODOO(self.node_id.odoo_host, self.node_id.odoo_protocol, self.node_id.odoo_port)
                noderpc.login(self.node_id.odoo_db, self.node_id.odoo_user, self.node_id.odoo_password)
            except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
                raise ValidationError(err)

            today = fields.Date.context_today(self.with_context())

            # TODO check hotel timezone
            checkin = fields.Date.from_string(today).strftime(
                DEFAULT_SERVER_DATE_FORMAT) if not self.checkin else fields.Date.from_string(self.checkin)

            checkout = (fields.Date.from_string(today) + timedelta(days=1)).strftime(
                DEFAULT_SERVER_DATE_FORMAT) if not self.checkout else fields.Date.from_string(self.checkout)

            if checkin >= checkout:
                checkout = checkin + timedelta(days=1)

            # rooms_availability = noderpc.env['hotel.room.type'].check_availability_room(checkin, checkout) # return str

            reservation_ids = noderpc.env['hotel.reservation'].search([
                ('reservation_line_ids.date', '>=', checkin),
                ('reservation_line_ids.date', '<', checkout),
                ('state', '!=', 'cancelled'),
                ('overbooking', '=', False)
            ])
            reservation_room_ids = noderpc.env['hotel.reservation'].browse(reservation_ids).mapped('room_id.id')

            room_type_availability = {}
            for room_type in self.node_id.room_type_ids:
                room_type_availability[room_type.id] = noderpc.env['hotel.room'].search_count([
                    ('id', 'not in', reservation_room_ids),
                    ('room_type_id', '=', room_type.remote_room_type_id)
                ])

            cmds = self.node_id.room_type_ids.mapped(lambda x: (0, False, {
                'room_type_id': x.id,
                'checkin': checkin,
                'checkout': checkout,
                'room_type_availability': room_type_availability[x.id],
            }))
            self.update({
                'checkin': checkin,
                'checkout': checkout,
                'room_type_wizard_ids': cmds,
            })

    @api.model
    def create_node_reservation(self):
        _logger.info('*** create_node_reservation(self) ***: %s', self)

#
#     def create_folio_node(self):
#         # Mediante un botón en el nodo creamos el folio indicando {partner_id, room_lines} pasandole con el
#         # formato o2m todas las reservas -room_lines- indicando {room_type_id, checkin, checkout, reservation_lines}
#         # reservation_lines en formato o2m usando el campo json_days de node.room.type.wizard.
#


class NodeRoomTypeWizard(models.TransientModel):
    _name = "node.room.type.wizard"
    _description = "Node Room Type Wizard"

    @api.model
    def _get_default_checkin(self):
        pass

    @api.model
    def _get_default_checkout(self):
        pass

    # node_id = fields.Many2one(related='node_reservation_wizard_id.node_id')

    node_reservation_wizard_id = fields.Many2one('hotel.node.reservation.wizard')

    room_type_id = fields.Many2one('hotel.node.room.type', 'Rooms Type')
    room_type_name = fields.Char('Name', related='room_type_id.name')
    room_type_availability = fields.Integer('Availability', compute="_compute_room_type_availability")
    rooms_qty = fields.Integer('Number of Rooms', default=0)

    checkin = fields.Date('Check In', required=True,
                          default=_get_default_checkin)
    checkout = fields.Date('Check Out', required=True,
                           default=_get_default_checkout)

#     price_unit #compute
#     price_total #compute
#     json_days #enchufar como texto literal la cadena devuelta por el método prepare_reservation_lines del hotel.reservation del nodo.(para que funcione
#                #es necesario que Darío modifique el método en el modulo Hotel haciendolo independiente del self.

    # compute and search fields, in the same order that fields declaration
    # @api.depends('node_id')
    # def _compute_room_type_availability(self):
    #     pass
        # for record in self:
        #     record.room_type_availability = 42
#
#     @api.onchange('checkin','checkout')
#     def onchange_dates(self):
#         # Conectar con nodo para traer dispo(availability) y precio por habitación(price_unit)
#         # availability: search de hotel.room.type.availability filtrando por room_type y date y escogiendo el min avail en el rango
#         # preci_unit y json_days: usando prepare_reservation_lines
#
#     @api.onchange('rooms_qty')
#     def _compute_price_total(self):
#         # Unidades x precio unidad (el precio de unidad ya incluye el conjunto de días)
#
