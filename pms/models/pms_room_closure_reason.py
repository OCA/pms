# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class RoomClosureReason(models.Model):
    _name = "room.closure.reason"
    _description = "Cause of out of service"

    name = fields.Char(
        required=True,
        translate=True,
        help="The name that identifies the room closure reason",
    )
    pms_property_ids = fields.Many2many(
        comodel_name="pms.property",
        relation="pms_room_closure_reason_pms_property_rel",
        column1="room_closure_reason_type_id",
        column2="pms_property_id",
        string="Properties",
        ondelete="restrict",
        help="Properties with access to the element;"
        " if not set, all properties can access",
    )
    description = fields.Text(
        help="Explanation of the reason for closing a room",
        translate=True,
    )
