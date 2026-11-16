# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    po_line_ids = fields.One2many(
        "purchase.order.line", "pms_property_id", string="Purchases"
    )
    po_line_count_calculated = fields.Integer(
        compute="_compute_po_line_count_calculated",
        string="PO Line(s)",
        readonly=True,
        copy=False,
    )

    @api.depends("po_line_ids")
    def _compute_po_line_count_calculated(self):
        for pms_property_id in self:
            pms_property_id.po_line_count_calculated = len(pms_property_id.po_line_ids)

    def action_open_po_line(self):
        view_id = self.env.ref("purchase.purchase_order_line_tree").id
        return {
            "name": self.env._("Purchase Order Lines"),
            "view_mode": "list",
            "view_id": view_id,
            "res_model": "purchase.order.line",
            "domain": [("id", "in", self.po_line_ids.ids)],
            "type": "ir.actions.act_window",
        }
