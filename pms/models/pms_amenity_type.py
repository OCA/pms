# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsRoomAmenityType(models.Model):
    _name = "pms.amenity.type"
    _description = "Amenities Type"

    # Fields declaration
    name = fields.Char("Amenity Type Name", translate=True, required=True)
    pms_property_ids = fields.Many2many(
        "pms.property", string="Properties", required=False, ondelete="restrict"
    )
    room_amenity_ids = fields.One2many(
        "pms.amenity", "room_amenity_type_id", "Amenities in this category"
    )
    active = fields.Boolean("Active", default=True)

    # TODO: Constrain coherence pms_property_ids with amenities pms_property_ids
