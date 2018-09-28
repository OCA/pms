# Copyright 2018  Pablo Q. Barriuso
# Copyright 2018  Alexandre Díaz
# Copyright 2018  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class HotelNodeReservationWizard(models.TransientModel):
    _name = "hotel.node.reservation.wizard"
    _description = "Hotel Node Reservation Wizard"

    node_id = fields.Many2one('project.project', 'Hotel')

    room_type_id = fields.Many2one('hotel.node.room.type', 'Rooms Type')
    room_type_name = fields.Char('Name', related='room_type_id.name')

    room_id = fields.Many2one('hotel.node.room', 'Rooms')

