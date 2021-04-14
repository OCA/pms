# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class RoomClosureReason(models.Model):
    _name = "room.closure.reason"
    _description = "Cause of out of service"

    name = fields.Char(
        string="Name",
        help="The name that identifies the room closure reason",
        required=True,
        translate=True,
    )
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        comodel_name="pms.property",
        relation="pms_room_closure_reason_pms_property_rel",
        column1="room_closure_reason_type_id",
        column2="pms_property_id",
        ondelete="restrict",
    )
    description = fields.Text(
        string="Description",
        help="Explanation of the reason for closing a room",
        translate=True,
    )
