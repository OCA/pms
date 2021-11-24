# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    contract_ids = fields.Many2many(
        "contract.contract",
        string="Contracts",
        compute="_compute_get_contracts",
        readonly=True,
        copy=False,
    )
    contract_count = fields.Integer(
        string="Contract Count",
        compute="_compute_get_contracts",
        readonly=True,
        copy=False,
    )

    @api.depends("service_ids")
    def _compute_get_contracts(self):
        for property in self:
            contracts = property.service_ids.mapped("contract_id")
            property.contract_ids = contracts
            property.contract_count = len(contracts)

    def action_view_contracts(self):
        action = self.env.ref("contract.action_customer_contract").read()[0]
        if len(self.contract_ids) > 1:
            action["domain"] = [("id", "in", self.contract_ids.ids)]
        elif self.contract_ids:
            action["views"] = [
                (self.env.ref("contract.contract_contract_form_view").id, "form")
            ]
            action["res_id"] = self.contract_ids.ids[0]
        return action
