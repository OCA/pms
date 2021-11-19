# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# Copyright 2018  Pablo Quesada
# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsRoom(models.Model):
    _name = "pms.room"
    _description = "Property Room"
    _order = "sequence, type_id, name"

    name = fields.Char(string="Room Name", help="Room Name", required=True)
    active = fields.Boolean(
        string="Active", help="Determines if room is active", default=True
    )
    sequence = fields.Integer(
        string="Sequence",
        help="Field used to change the position of the rooms in tree view."
        "Changing the position changes the sequence",
        default=0,
    )
    property_id = fields.Many2one(
        string="Property",
        required=True,
        comodel_name="pms.property",
        ondelete="restrict",
    )
    type_id = fields.Many2one(
        string="Room Type",
        help="Unique room type for the rooms",
        required=True,
        comodel_name="pms.room.type",
        ondelete="restrict",
    )
    capacity = fields.Integer(
        string="Capacity", help="The maximum number of people that can occupy a room"
    )
    area = fields.Float(string="Area")
    _sql_constraints = [
        (
            "room_property_unique",
            "unique(name, property_id)",
            "You cannot have more 2 rooms with the same name in the same property.",
        )
    ]
