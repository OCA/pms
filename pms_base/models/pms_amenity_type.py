# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsRoomAmenityType(models.Model):
    _name = "pms.amenity.type"
    _description = "Amenity Type"

    active = fields.Boolean(
        string="Active", help="Determines if amenity type is active", default=True
    )
    name = fields.Char(string="Name", required=True, translate=True)
