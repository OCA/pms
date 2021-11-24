# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ContractContract(models.Model):
    _inherit = "contract.contract"

    property_ids = fields.Many2many(
        "pms.property",
        string="Properties",
        compute="_compute_get_properties",
        readonly=True,
        copy=False,
    )
    property_count = fields.Integer(
        string="Property Count",
        compute="_compute_get_properties",
        readonly=True,
        copy=False,
    )

    @api.depends("contract_line_ids")
    def _compute_get_properties(self):
        for contract in self:
            properties = contract.contract_line_ids.mapped("property_id")
            contract.property_ids = properties
            contract.property_count = len(properties)

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
