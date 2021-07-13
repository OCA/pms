# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ChannelWubookPmsAvailabilityPlanRuleBinding(models.Model):
    _name = "channel.wubook.pms.availability.plan.rule"
    _inherit = "channel.wubook.binding"
    _inherits = {"pms.availability.plan.rule": "odoo_id"}

    external_id = fields.Char(string="External ID")

    odoo_id = fields.Many2one(
        comodel_name="pms.availability.plan.rule",
        string="Odoo ID",
        required=True,
        ondelete="cascade",
    )

    channel_wubook_availability_plan_id = fields.Many2one(
        comodel_name="channel.wubook.pms.availability.plan",
        string="Wubook Plan ID",
        required=True,
        ondelete="cascade",
    )

    no_ota = fields.Boolean(
        string="No OTA",
        default=False,
        help="Set zero availability to the connected OTAs "
        "even when the availability is positive,"
        "except to the Online Reception (booking engine)",
    )

    inconsistent_binding_rules = fields.Many2many(
        readonly=True,
        store=False,
        comodel_name="channel.wubook.pms.availability.plan.rule",
        compute="_compute_inconsistent_binding_rules",
    )

    @api.depends("no_ota")
    def _compute_inconsistent_binding_rules(self):
        for rec in self:
            inconsistent_binding_rules = self.search(
                [
                    ("id", "not in", rec.ids),
                    ("room_type_id", "=", rec.room_type_id.id),
                    ("date", "=", rec.date),
                    ("backend_id", "=", rec.backend_id.id),
                    ("no_ota", "!=", rec.no_ota),
                ]
            )
            inconsistent_binding_rules.no_ota = rec.no_ota
            rec.inconsistent_binding_rules = inconsistent_binding_rules

    @api.constrains("pms_property_id")
    def _check_pms_property_id(self):
        for rec in self:
            if rec.pms_property_id != rec.backend_id.pms_property_id:
                raise ValidationError(
                    _("The property on the rule must match the ones on the bindings")
                )

    @api.model
    def create(self, vals):
        channel_wubook_availability_plan_id = vals[
            "channel_wubook_availability_plan_id"
        ]
        binding = self.env["channel.wubook.pms.availability.plan"].browse(
            channel_wubook_availability_plan_id
        )
        vals["availability_plan_id"] = binding.odoo_id.id
        binding = super().create(vals)
        return binding
