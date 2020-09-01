# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsRoomTypeClass(models.Model):
    """Before creating a 'room type_class', you need to consider the following:
    With the term 'room type class' is meant a physical class of
    residential accommodation: for example, a Room, a Bed, an Apartment,
    a Tent, a Caravan...
    """

    _name = "pms.room.type.class"
    _description = "Room Type Class"
    _order = "sequence, name, code_class"

    # Fields declaration
    name = fields.Char("Class Name", required=True, translate=True)
    # Relationship between models
    pms_property_ids = fields.Many2many(
        "pms.property", string="Properties", required=False, ondelete="restrict"
    )
    room_type_ids = fields.One2many("pms.room.type", "class_id", "Types")
    code_class = fields.Char("Code")
    active = fields.Boolean("Active", default=True)
    sequence = fields.Integer("Sequence", default=0)

    _sql_constraints = [
        ("code_class_unique", "unique(code_class)", "Room Class Code must be unique!")
    ]
