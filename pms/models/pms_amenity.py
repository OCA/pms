# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsRoomAmenity(models.Model):
    _name = "pms.amenity"
    _description = "Room amenity"

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
        relation="pms_amenity_pms_property_rel",
        column1="amenity_type_id",
        column2="pms_property_id",
    )
    pms_amenity_type_id = fields.Many2one(
        string="Amenity Category",
        help="Segment the amenities by categories (multimedia, comfort, etc ...)",
        comodel_name="pms.amenity.type",
        domain="['|', ('pms_property_ids', '=', False),('pms_property_ids', 'in', "
        "pms_property_ids)]",
    )
    default_code = fields.Char(
        string="Internal Reference", help="Internal unique identifier of the amenity"
    )

    @api.constrains(
        "pms_amenity_type_id",
        "pms_property_ids",
    )
    def _check_property_integrity(self):
        for rec in self:
            if rec.pms_amenity_type_id and rec.pms_amenity_type_id.pms_property_ids:
                res = rec.pms_property_ids - rec.pms_amenity_type_id.pms_property_ids
                if res:
                    raise ValidationError(_("Property not allowed"))
