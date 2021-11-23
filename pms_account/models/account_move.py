# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    property_ids = fields.Many2many(
        "pms.property",
        compute="_compute_pms_property_ids",
        string="Properties associated to this invoice",
    )
    property_count = fields.Integer(
        string="Properties", compute="_compute_pms_property_ids"
    )

    @api.depends("line_ids")
    def _compute_pms_property_ids(self):
        for invoice in self:
            properties = self.env["pms.property"].search(
                [("invoice_line_ids", "in", invoice.line_ids.ids)]
            )
            invoice.property_ids = properties
            invoice.property_count = len(invoice.property_ids)

    def action_view_pms_property(self):
        action = self.env.ref("pms_base.action_pms_property").read()[0]
        if self.property_count > 1:
            action["domain"] = [("id", "in", self.property_ids.ids)]
        elif self.property_ids:
            action["views"] = [
                (self.env.ref("pms_base.view_pms_property_form").id, "form")
            ]
            action["res_id"] = self.property_ids[0].id
        return action
