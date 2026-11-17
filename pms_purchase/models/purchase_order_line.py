# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    pms_property_id = fields.Many2one("pms.property", string="Property")

    @api.depends(
        "product_id",
        "order_id.partner_id",
        "pms_property_id",
        "pms_property_id.analytic_id",
    )
    def _compute_analytic_distribution(self):
        res = super()._compute_analytic_distribution()
        for purchase_line_id in self:
            if not purchase_line_id.pms_property_id:
                continue
            analytic_id = purchase_line_id.pms_property_id.analytic_id
            if analytic_id:
                purchase_line_id.analytic_distribution = {str(analytic_id.id): 100}
            else:
                purchase_line_id.analytic_distribution = {}
        return res
