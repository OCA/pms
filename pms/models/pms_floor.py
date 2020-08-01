# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsFloor(models.Model):
    _name = "pms.floor"
    _description = "Ubication"

    # Fields declaration
    name = fields.Char(
        "Ubication Name", translate=True, size=64, required=True, index=True
    )
    pms_property_ids = fields.Many2many(
        "pms.property", string="Properties", required=False, ondelete="restrict"
    )
    sequence = fields.Integer("Sequence")
