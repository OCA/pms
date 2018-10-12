# Copyright 2018  Pablo Q. Barriuso
# Copyright 2018  Alexandre Díaz
# Copyright 2018  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import wdb
import logging
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.tools import (
    misc,
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)

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

    partner_id = fields.Many2one('res.partner', string="Customer")

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
            today = fields.Date.context_today(self.with_context())

            # TODO check hotel timezone
            checkin = fields.Date.from_string(today).strftime(
                DEFAULT_SERVER_DATE_FORMAT) if not self.checkout else fields.Date.from_string(self.checkin)

            checkout = (fields.Date.from_string(today) + timedelta(days=1)).strftime(
                DEFAULT_SERVER_DATE_FORMAT) if not self.checkout else fields.Date.from_string(self.checkout)

            if checkin >= checkout:
                checkout = checkin + timedelta(days=1)

            room_type_ids = self.env['hotel.node.room.type'].search([('node_id','=',self.node_id.id)])
            cmds = room_type_ids.mapped(lambda x: (0, False, {
                'room_type_id': x.id,
                'checkin': checkin,
                'checkout': checkout,
            }))
            self.update({
                'checkin': checkin,
                'checkout': checkout,
                'room_type_wizard_ids': cmds,
            })


class NodeRoomTypeWizard(models.TransientModel):
    _name = "node.room.type.wizard"
    _description = "Node Room Type Wizard"

    @api.model
    def _get_default_checkin(self):
        pass

    @api.model
    def _get_default_checkout(self):
        pass

    node_reservation_wizard_id = fields.Many2one('hotel.node.reservation.wizard')

    room_type_id = fields.Many2one('hotel.node.room.type', 'Rooms Type')

    room_type_name = fields.Char('Name', related='room_type_id.name')
    room_type_availability = fields.Integer('Availability', compute="_compute_room_type_availability")


    rooms_qty = fields.Integer('Number of Rooms', default=0)

    checkin = fields.Date('Check In', required=True,
                          default=_get_default_checkin)
    checkout = fields.Date('Check Out', required=True,
                           default=_get_default_checkout)

    # compute and search fields, in the same order that fields declaration
    @api.multi
    def _compute_room_type_availability(self):
        for record in self:
            record.room_type_availability = 42;

