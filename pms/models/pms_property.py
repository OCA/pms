# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsProperty(models.Model):
    _name = "pms.property"
    _description = "Property"
    _inherits = {"res.partner": "partner_id"}
    _check_company_auto = True

    # Fields declaration
    partner_id = fields.Many2one(
        "res.partner", "Property", required=True, delegate=True, ondelete="cascade"
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        help="The company that owns or operates this property.",
    )
    user_ids = fields.Many2many(
        "res.users",
        "pms_property_users_rel",
        "pms_property_id",
        "user_id",
        string="Accepted Users",
    )
    room_type_ids = fields.One2many("pms.room.type", "pms_property_id", "Room Types")
    room_ids = fields.One2many("pms.room", "pms_property_id", "Rooms")
    default_pricelist_id = fields.Many2one(
        "product.pricelist",
        string="Product Pricelist",
        required=True,
        help="The default pricelist used in this property.",
    )
    default_restriction_id = fields.Many2one(
        "pms.room.type.restriction",
        "Restriction Plan",
        required=True,
        help="The default restriction plan used in this property.",
    )
    default_arrival_hour = fields.Char(
        "Arrival Hour (GMT)", help="HH:mm Format", default="14:00"
    )
    default_departure_hour = fields.Char(
        "Departure Hour (GMT)", help="HH:mm Format", default="12:00"
    )
    default_cancel_policy_days = fields.Integer("Cancellation Days")
    default_cancel_policy_percent = fields.Float("Percent to pay")
    folio_sequence_id = fields.Many2one(
        "ir.sequence", "Folio Sequence", check_company=True, copy=False
    )

    # Constraints and onchanges
    @api.constrains("default_arrival_hour", "default_departure_hour")
    def _check_hours(self):
        r = re.compile("[0-2][0-9]:[0-5][0-9]")
        if not r.match(self.default_arrival_hour):
            raise ValidationError(_("Invalid arrival hour (Format: HH:mm)"))
        if not r.match(self.default_departure_hour):
            raise ValidationError(_("Invalid departure hour (Format: HH:mm)"))
