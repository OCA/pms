# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsAmenity(models.Model):
    _name = "pms.amenity"
    _description = "Property Amenity"

    active = fields.Boolean(
        string="Active", help="Determines if amenity is active", default=True
    )
    name = fields.Char(
        string="Name", help="Name of the amenity", required=True, translate=True
    )
    property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the amenity",
        comodel_name="pms.property",
        ondelete="restrict",
        relation="pms_property_amenity_rel",
        column1="amenity_id",
        column2="property_id",
    )
    type_id = fields.Many2one(
        string="Type",
        help="Organize amenities by type (multimedia, comfort, etc ...)",
        comodel_name="pms.amenity.type",
    )
    default_code = fields.Char(
        string="Internal Reference", help="Internal unique identifier of the amenity"
    )
