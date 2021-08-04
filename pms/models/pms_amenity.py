# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsRoomAmenity(models.Model):
    _name = "pms.amenity"
    _description = "Room amenity"
    _check_pms_properties_auto = True

    active = fields.Boolean(
        string="Active",
        help="Determines if amenity is active",
        default=True,
    )
    name = fields.Char(
        string="Amenity Name",
        help="Amenity Name",
        required=True,
        translate=True,
    )
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        comodel_name="pms.property",
        ondelete="restrict",
        relation="pms_amenity_pms_property_rel",
        column1="amenity_id",
        column2="pms_property_id",
        check_pms_properties=True,
    )
    pms_amenity_type_id = fields.Many2one(
        string="Amenity Category",
        help="Segment the amenities by categories (multimedia, comfort, etc ...)",
        comodel_name="pms.amenity.type",
        check_pms_properties=True,
    )
    default_code = fields.Char(
        string="Internal Reference", help="Internal unique identifier of the amenity"
    )
    is_add_code_room_name = fields.Boolean(
        string="Add in room name",
        help="True if the Internal Reference should appear in the display name of the rooms",
    )
