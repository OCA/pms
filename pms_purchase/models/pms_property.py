# Copyright (c) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    po_line_ids = fields.One2many(
        "purchase.order.line", "pms_property_id", string="Purchases"
    )
    po_line_count = fields.Integer(
        compute="_compute_po_line_count", string="PO Line(s)", readonly=True, copy=False
    )

    @api.depends("po_line_ids")
    def _compute_po_line_count(self):
        for pms_property in self:
            pms_property.po_line_count = len(pms_property.po_line_ids)

    def action_open_po_line(self):
        view_id = self.env.ref("purchase.purchase_order_line_tree").id
        return {
            "name": _("Purchase Order Lines"),
            "view_mode": "tree",
            "view_id": view_id,
            "res_model": "purchase.order.line",
            "domain": [("id", "in", self.po_line_ids.ids)],
            "type": "ir.actions.act_window",
        }
