# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    pms_property_id = fields.Many2one("pms.property", string="Property")

    @api.onchange("pms_property_id")
    def _onchange_pms_property_id(self):
        for rec in self:
            if rec.pms_property_id and rec.pms_property_id.analytic_id:
                rec.analytic_distribution = {
                    str(rec.pms_property_id.analytic_id.id): 100
                }
            else:
                rec.analytic_distribution = {}
