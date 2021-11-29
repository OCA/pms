# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    property_ids = fields.Many2many(
        "pms.property",
        string="Properties",
        copy=False,
    )
    property_count = fields.Integer(
        string="Property Count",
        compute="_compute_propert_count",
        readonly=True,
        copy=False,
    )

    @api.depends("property_ids")
    def _compute_property_count(self):
        for lead in self:
            lead.property_count = len(lead.property_ids)

    def action_view_properties(self):
        action = self.env.ref("pms_base.action_pms_property").read()[0]
        if self.property_count > 1:
            action["domain"] = [("id", "in", self.property_ids.ids)]
        elif self.property_ids:
            action["views"] = [
                (self.env.ref("pms_base.view_pms_property_form").id, "form")
            ]
            action["res_id"] = self.property_ids.ids[0]
        return action
