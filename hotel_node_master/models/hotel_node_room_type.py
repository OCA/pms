# Copyright 2018  Pablo Q. Barriuso
# Copyright 2018  Alexandre Díaz
# Copyright 2018  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class HotelNodeRoomType(models.Model):
    _name = "hotel.node.room.type"
    _description = "Room Type"

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=0)

    name = fields.Char(required=True, translate=True)

    remote_room_type_id = fields.Integer(require=True, invisible=True, copy=False,
                                    help="ID of the target record in the remote database")

    room_ids = fields.One2many('hotel.node.room', 'room_type_id', 'Rooms')

    node_id = fields.Many2one('project.project', 'Hotel', required=True)
