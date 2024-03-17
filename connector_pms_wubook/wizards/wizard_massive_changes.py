# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models


class AvailabilityWizard(models.TransientModel):
    _inherit = "pms.massive.changes.wizard"

    inconsistent_rule_ids = fields.Many2many(
        readonly=True,
        store=False,
        comodel_name="pms.availability.plan.rule",
        compute="_compute_inconsistent_rules",
    )

    inconsistent_rule_count = fields.Integer(
        readonly=True,
        store=False,
        compute="_compute_inconsistent_rules",
    )

    @api.depends("rules_to_overwrite")
    def _compute_inconsistent_rules(self):
        for rec in self:
            if rec.apply_quota or rec.apply_max_avail:
                backend_availability_plans = self.env["pms.availability.plan"].search(
                    [
                        ("id", "not in", rec.availability_plan_ids.ids),
                        ("rule_ids.pms_property_id", "in", rec.pms_property_ids.ids),
                        (
                            "channel_wubook_bind_ids.backend_id",
                            "in",
                            rec.availability_plan_ids.channel_wubook_bind_ids.backend_id.mapped(
                                "id"
                            ),
                        ),
                    ]
                )
                inconsistent_rules = rec._rules_to_overwrite_by_plans(
                    backend_availability_plans
                )
                if rec.apply_quota:
                    inconsistent_rules.filtered(
                        lambda x: x.quota != rec.quota
                    ).quota = rec.quota
                if rec.apply_max_avail:
                    inconsistent_rules.filtered(
                        lambda x: x.max_avail != rec.max_avail
                    ).max_avail = rec.max_avail
                rec.inconsistent_rule_ids = inconsistent_rules
                rec.inconsistent_rule_count = len(inconsistent_rules)
            else:
                rec.inconsistent_rule_ids = False
                rec.inconsistent_rule_count = 0
