# Copyright (c) 2021 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    lead_ids = fields.Many2many(
        "crm.lead",
        relation="crm_lead_pms_property_rel",
        column1="property_id",
        column2="lead_id",
        string="Leads",
        copy=False,
    )
    lead_count = fields.Integer(
        compute="_compute_lead_count",
        readonly=True,
        copy=False,
    )

    @api.depends("lead_ids")
    def _compute_lead_count(self):
        for rec in self:
            rec.lead_count = len(rec.lead_ids)

    def action_view_leads(self):
        action = self.env.ref("crm.crm_lead_all_leads").read()[0]
        if self.lead_count > 1:
            action["domain"] = [("id", "in", self.lead_ids.ids)]
        elif self.lead_ids:
            action["views"] = [(self.env.ref("crm.crm_lead_view_form").id, "form")]
            action["res_id"] = self.lead_ids.ids[0]
        return action
