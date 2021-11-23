# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    asset_ids = fields.One2many(
        "account.asset",
        inverse_name="property_id",
        string="Assets",
        copy=False,
    )
    asset_count = fields.Integer(
        string="Asset Count",
        compute="_compute_asset_count",
        readonly=True,
        copy=False,
    )

    def _compute_asset_count(self):
        for property in self:
            property.asset_count = len(property.asset_ids)

    def action_view_assets(self):
        action = self.env.ref("account_asset_management.account_asset_action").read()[0]
        if len(self.asset_ids) > 1:
            action["domain"] = [("id", "in", self.asset_ids.ids)]
        elif self.asset_ids:
            action["views"] = [
                (
                    self.env.ref("account_asset_management.account_asset_view_form").id,
                    "form",
                )
            ]
            action["res_id"] = self.asset_ids.ids[0]
        return action
