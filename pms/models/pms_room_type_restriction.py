# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PmsRoomTypeRestriction(models.Model):
    """The room type restriction is used as a daily restriction plan for room types
    and therefore is related only with one property."""

    _name = "pms.room.type.restriction"
    _description = "Reservation restriction plan"

    # Default methods
    @api.model
    def _get_default_pms_property(self):
        return self.env.user.pms_property_id or None

    # Fields declaration
    name = fields.Char("Restriction Plan Name", required=True)
    pms_property_id = fields.Many2one(
        "pms.property",
        "Property",
        ondelete="restrict",
        default=_get_default_pms_property,
    )
    item_ids = fields.One2many(
        "pms.room.type.restriction.item",
        "restriction_id",
        string="Restriction Items",
        copy=True,
    )
    active = fields.Boolean(
        "Active",
        default=True,
        help="If unchecked, it will allow you to hide the "
        "restriction plan without removing it.",
    )
