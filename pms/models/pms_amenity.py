# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsRoomAmenity(models.Model):
    _name = "pms.amenity"
    _description = "Room amenities"

    # Fields declaration
    name = fields.Char("Amenity Name", translate=True, required=True)
    pms_property_ids = fields.Many2many(
        "pms.property", string="Properties", required=False, ondelete="restrict"
    )
    room_amenity_type_id = fields.Many2one("pms.amenity.type", "Amenity Category")
    default_code = fields.Char("Internal Reference")
    active = fields.Boolean("Active", default=True)

    # TODO: Constrain coherence pms_property_ids with amenity types pms_property_ids
