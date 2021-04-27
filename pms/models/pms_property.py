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

    partner_id = fields.Many2one(
        string="Property",
        help="Current property",
        comodel_name="res.partner",
        required=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(
        string="Company",
        help="The company that owns or operates this property.",
        comodel_name="res.company",
        required=True,
        check_pms_properties=True,
    )
    user_ids = fields.Many2many(
        string="Accepted Users",
        help="Field related to res.users. Allowed users on the property",
        comodel_name="res.users",
        relation="pms_property_users_rel",
        column1="pms_property_id",
        column2="user_id",
    )
    room_ids = fields.One2many(
        string="Rooms",
        help="Rooms that a property has.",
        comodel_name="pms.room",
        inverse_name="pms_property_id",
    )
    default_pricelist_id = fields.Many2one(
        string="Product Pricelist",
        help="The default pricelist used in this property.",
        comodel_name="product.pricelist",
        required=True,
        default=lambda self: self.env.ref("product.list0").id,
    )
    default_arrival_hour = fields.Char(
        string="Arrival Hour", help="HH:mm Format", default="14:00"
    )
    default_departure_hour = fields.Char(
        string="Departure Hour", help="HH:mm Format", default="12:00"
    )
    folio_sequence_id = fields.Many2one(
        string="Folio Sequence",
        help="The sequence that formed the name of the folio.",
        check_company=True,
        copy=False,
        comodel_name="ir.sequence",
    )
    reservation_sequence_id = fields.Many2one(
        string="Reservation Sequence",
        help="The sequence that formed the name of the reservation.",
        check_company=True,
        copy=False,
        comodel_name="ir.sequence",
    )
    checkin_sequence_id = fields.Many2one(
        string="Checkin Sequence",
        help="Field used to create the name of the checkin partner",
        check_company=True,
        copy=False,
        comodel_name="ir.sequence",
    )

    tz = fields.Selection(
        string="Timezone",
        help="This field is used to determine de timezone of the property.",
        required=True,
        default=lambda self: self.env.user.tz or "UTC",
        selection=_tz_get,
    )

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

    def date_property_timezone(self, dt):
        self.ensure_one()
        tz_property = self.tz
        dt = pytz.timezone(tz_property).localize(dt)
        dt = dt.replace(tzinfo=None)
        dt = pytz.timezone(self.env.user.tz).localize(dt)
        dt = dt.astimezone(pytz.utc)
        dt = dt.replace(tzinfo=None)
        return dt

    def _get_payment_methods(self):
        self.ensure_one()
        payment_methods = self.env["account.journal"].search(
            [
                "&",
                ("type", "in", ["cash", "bank"]),
                "|",
                ("pms_property_ids", "in", self.id),
                "|",
                "&",
                ("pms_property_ids", "=", False),
                ("company_id", "=", self.company_id.id),
                "&",
                ("pms_property_ids", "=", False),
                ("company_id", "=", False),
            ]
        )
        return payment_methods

    @api.model
    def create(self, vals):
        name = vals.get("name")
        if "folio_sequence_id" not in vals or not vals.get("folio_sequence_id"):
            folio_sequence = self.env["ir.sequence"].create(
                {
                    "name": "PMS Folio " + name,
                    "code": "pms.folio",
                    "prefix": "F/%(y)s",
                    "suffix": "%(sec)s",
                    "padding": 4,
                    "company_id": vals.get("company_id"),
                }
            )
            vals.update({"folio_sequence_id": folio_sequence.id})
        if "reservation_sequence_id" not in vals or not vals.get(
            "reservation_sequence_id"
        ):
            reservation_sequence = self.env["ir.sequence"].create(
                {
                    "name": "PMS Reservation " + name,
                    "code": "pms.reservation",
                    "prefix": "R/%(y)s",
                    "suffix": "%(sec)s",
                    "padding": 4,
                    "company_id": vals.get("company_id"),
                }
            )
            vals.update({"reservation_sequence_id": reservation_sequence.id})
        if "checkin_sequence_id" not in vals or not vals.get("checkin_sequence_id"):
            checkin_sequence = self.env["ir.sequence"].create(
                {
                    "name": "PMS Checkin " + name,
                    "code": "pms.checkin.partner",
                    "prefix": "C/%(y)s",
                    "suffix": "%(sec)s",
                    "padding": 4,
                    "company_id": vals.get("company_id"),
                }
            )
            vals.update({"checkin_sequence_id": checkin_sequence.id})
        record = super(PmsProperty, self).create(vals)
        return record
