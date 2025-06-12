# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class PmsAvailabilityPlan(models.Model):
    """The room type availability is used as a daily availability plan for room types
    and therefore is related only with one property."""

    _name = "pms.availability.plan"
    _description = "Reservation availability plan"
    _check_pms_properties_auto = True

    name = fields.Char(
        string="Availability Plan Name", help="Name of availability plan", required=True
    )
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        comodel_name="pms.property",
        ondelete="restrict",
        relation="pms_availability_plan_pms_property_rel",
        column1="availability_plan_id",
        column2="pms_property_id",
        check_pms_properties=True,
    )
    pms_pricelist_ids = fields.One2many(
        string="Pricelists",
        help="Pricelists of the availability plan ",
        comodel_name="product.pricelist",
        inverse_name="availability_plan_id",
        check_pms_properties=True,
        domain="[('is_pms_available', '=', True)]",
    )

    rule_ids = fields.One2many(
        string="Availability Rules",
        help="Rules in a availability plan",
        comodel_name="pms.availability.plan.rule",
        inverse_name="availability_plan_id",
        check_pms_properties=True,
    )

    active = fields.Boolean(
        help="If unchecked, it will allow you to hide the "
        "Availability plan without removing it.",
        default=True,
    )

    @classmethod
    def any_rule_applies(cls, checkin, checkout, item):
        if isinstance(checkin, str):
            checkin = datetime.datetime.strptime(
                checkin, DEFAULT_SERVER_DATE_FORMAT
            ).date()
        if isinstance(checkout, str):
            checkout = datetime.datetime.strptime(
                checkout, DEFAULT_SERVER_DATE_FORMAT
            ).date()
        reservation_len = (checkout - checkin).days
        return any(
            [
                (0 < item.max_stay < reservation_len and item.date != checkout),
                (0 < item.min_stay > reservation_len and item.date != checkout),
                (0 < item.max_stay_arrival < reservation_len and checkin == item.date),
                (0 < item.min_stay_arrival > reservation_len and checkin == item.date),
                (item.closed and item.date != checkout),
                (item.closed_arrival and checkin == item.date),
                (item.closed_departure and checkout == item.date),
                ((item.quota == 0 or item.max_avail == 0) and item.date != checkout),
            ]
        )

    @api.model
    def update_quota(
        self,
        pricelist_id,
        room_type_id,
        date,
        pms_property_id,
    ):
        if pricelist_id and room_type_id and date:
            rule = self.env["pms.availability.plan.rule"].search(
                [
                    ("availability_plan_id.pms_pricelist_ids", "in", pricelist_id),
                    ("room_type_id", "=", room_type_id),
                    ("date", "=", date),
                    ("pms_property_id", "=", pms_property_id),
                ]
            )
            # applies a rule
            if rule:
                rule.ensure_one()
                if rule and rule.quota != -1 and rule.quota > 0:
                    rule.quota -= 1
                    return True
        return False

    # Action methods
    def open_massive_changes_wizard(self):
        if self.ensure_one():
            return {
                "view_type": "form",
                "view_mode": "form",
                "name": "Massive changes on Availability Plan: " + self.name,
                "res_model": "pms.massive.changes.wizard",
                "target": "new",
                "type": "ir.actions.act_window",
                "context": {
                    "availability_plan_id": self.id,
                },
            }
