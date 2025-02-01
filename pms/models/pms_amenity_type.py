# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsRoomAmenityType(models.Model):
    _name = "pms.amenity.type"
    _description = "Amenity Type"
    _check_pms_properties_auto = True

    active = fields.Boolean(
        help="Determines if amenity type is active",
        default=True,
    )
    name = fields.Char(
        string="Amenity Type Name",
        help="Amenity Type Name",
        required=True,
        translate=True,
    )
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        comodel_name="pms.property",
        ondelete="restrict",
        relation="pms_amenity_type_pms_property_rel",
        column1="amenity_type_id",
        column2="pms_property_id",
        check_pms_properties=True,
    )
    pms_amenity_ids = fields.One2many(
        string="Amenities In This Category",
        help="Amenities included in this type",
        comodel_name="pms.amenity",
        inverse_name="pms_amenity_type_id",
        check_pms_properties=True,
    )
