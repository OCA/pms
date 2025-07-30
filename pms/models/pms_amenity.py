# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# Copyright 2025 Ecosoft Co., Ltd. (http://ecosoft.co.th)

# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PmsRoomAmenity(models.Model):
    _name = "pms.amenity"
    _description = "Room Amenity"
    _check_pms_properties_auto = True

    active = fields.Boolean(
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
        comodel_name="pms.property",
        relation="pms_amenity_pms_property_rel",
        column1="amenity_id",
        column2="pms_property_id",
        string="Properties",
        ondelete="restrict",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        check_pms_properties=True,
    )
    pms_amenity_type_id = fields.Many2one(
        comodel_name="pms.amenity.type",
        string="Amenity Category",
        index=True,
        help="Segment the amenities by categories (multimedia, comfort, etc ...)",
        check_pms_properties=True,
    )
    default_code = fields.Char(
        string="Internal Reference", help="Internal unique identifier of the amenity"
    )
    is_add_code_room_name = fields.Boolean(
        string="Display with Internal Reference",
        help="True if the Internal Reference should appear in "
        "the display name of the rooms",
    )
