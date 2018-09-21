# Copyright 2018  Pablo Q. Barriuso
# Copyright 2018  Alexandre Díaz
# Copyright 2018  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import wdb
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HotelNodeRoomType(models.Model):
    _name = "hotel.node.room.type"
    _description = "Room Type"

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=0)

    name = fields.Char(required=True, translate=True)

    remote_room_type_id = fields.Integer(require=True, invisible=True, copy=False, readonly=True,
                                         help="ID of the target record in the remote database")

    room_ids = fields.One2many('hotel.node.room', 'room_type_id', 'Rooms')

    node_id = fields.Many2one('project.project', 'Hotel', required=True)

    _sql_constraints = [
        ('db_remote_room_type_id_uniq', 'unique (remote_room_type_id, node_id)',
         'The Room Type must be unique within the Node!'),
    ]

    @api.onchange('node_id')
    def _onchange_node_id(self):
        if self.node_id:
            return {'domain': {'room_ids': [('room_ids', 'in', self.room_ids.ids)]}}

        return {'domain': {'room_ids': []}}

    @api.model
    def create(self, vals):
        """
        :param dict vals: the model's fields as a dictionary
        :return: new hotel room type record created.
        :raise: ValidationError
        """
        _logger.warning("This fuction is not yet implemented for remote create.")
        return super().create(vals)

    @api.multi
    def write(self, vals):
        """
        :param dict vals: a dictionary of fields to update and the value to set on them.
        :raise: ValidationError
        """
        for rec in self:
            if 'node_id' in vals and vals['node_id'] != rec.node_id.id:
                msg = _("Changing a room type between nodes is not allowed. Please create a new room type instead.")
                _logger.error(msg)
                raise ValidationError(msg)

        _logger.warning("This fuction is not yet implemented for remote update.")
        return super().write(vals)

    @api.multi
    def unlink(self):
        """
        :raise: ValidationError
        """
        _logger.warning("This fuction is not yet implemented for remote delete.")
        return super().unlink()
