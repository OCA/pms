# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsRoomAmenity(models.Model):
    _name = "pms.amenity"
    _description = "Room amenities"

    # Fields declaration
    name = fields.Char("Amenity Name", translate=True, required=True)
    pms_property_ids = fields.Many2many(
        "pms.property",
        string="Properties",
        required=False,
        ondelete="restrict",
    )
    room_amenity_type_id = fields.Many2one(
        "pms.amenity.type",
        "Amenity Category",
        domain="['|', ('pms_property_ids', '=', False),('pms_property_ids', 'in', "
        "pms_property_ids)]",
    )
    default_code = fields.Char("Internal Reference")
    active = fields.Boolean("Active", default=True)

    # TODO: Constrain coherence pms_property_ids with amenity types pms_property_ids
    allowed_property_ids = fields.Many2many(
        "pms.property",
        "allowed_amenity_move_rel",
        "amenity_id",
        "property_id",
        string="Allowed Properties",
        store=True,
        readonly=True,
        compute="_compute_allowed_property_ids",
    )

    @api.depends(
        "room_amenity_type_id.pms_property_ids",
    )
    def _compute_allowed_property_ids(self):
        for amenity in self:
            if amenity.room_amenity_type_id.pms_property_ids:
                amenity.allowed_property_ids = (
                    amenity.room_amenity_type_id.pms_property_ids
                )
            else:
                amenity.allowed_property_ids = False

    @api.constrains(
        "allowed_property_ids",
        "pms_property_ids",
    )
    def _check_property_integrity(self):
        for rec in self:
            if rec.pms_property_ids and rec.allowed_property_ids:
                for prop in rec.pms_property_ids:
                    if prop not in rec.allowed_property_ids:
                        raise ValidationError(_("Property not allowed in amenity type"))
