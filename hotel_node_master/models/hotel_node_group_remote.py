# Copyright 2018  Pablo Q. Barriuso
# Copyright 2018  Alexandre Díaz
# Copyright 2018  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class HotelNodeGroupRemote(models.Model):
    _name = "hotel.node.group.remote"
    _description = "Remote Access Groups IDs"

    node_id = fields.Many2one('project.project', 'Hotel', required=True)
    group_id = fields.Many2one('hotel.node.group', 'Group', require=True)
    name = fields.Char(related='group_id.name')
    remote_group_id = fields.Integer(require=True, copy=False, readonly=True,
                                    help="ID of the target record in the remote database")

    _sql_constraints = [
        ('node_remote_group_id_uniq', 'unique (node_id, remote_group_id)',
         'The remote identifier of the group must be unique within a Node!')
    ]
