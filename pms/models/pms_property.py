# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.base.models.res_partner import _tz_get


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
    tz = fields.Selection(
        _tz_get,
        string="Timezone",
        required=True,
        default=lambda self: self.env.user.tz or "UTC",
        help="This field is used in order to define \
         in which timezone the arrival/departure will work.",
    )

    # Constraints and onchanges
    @api.constrains("default_arrival_hour")
    def _check_arrival_hour(self):
        for record in self:
            try:
                time.strptime(record.default_arrival_hour, "%H:%M")
                return True
            except ValueError:
                raise ValidationError(
                    _(
                        "Format Arrival Hour (HH:MM) Error: %s",
                        record.default_arrival_hour,
                    )
                )

    @api.constrains("default_departure_hour")
    def _check_departure_hour(self):
        for record in self:
            try:
                time.strptime(record.default_departure_hour, "%H:%M")
                return True
            except ValueError:
                raise ValidationError(
                    _(
                        "Format Departure Hour (HH:MM) Error: %s",
                        record.default_departure_hour,
                    )
                )

    def date_property_timezone(self, date):
        self.ensure_one()
        tz_property = self.tz
        date = pytz.timezone(tz_property).localize(date)
        date = date.replace(tzinfo=None)
        date = pytz.timezone(self.env.user.tz).localize(date)
        date = date.astimezone(pytz.utc)
        date = date.replace(tzinfo=None)
        return date
