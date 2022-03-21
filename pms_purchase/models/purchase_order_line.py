# Copyright (c) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    pms_property_id = fields.Many2one("pms.property", string="Property")

    @api.onchange("pms_property_id")
    def _onchange_pms_property_id(self):
        account_analytic_id = False
        for rec in self:
            if rec.pms_property_id and rec.pms_property_id.analytic_id:
                account_analytic_id = rec.pms_property_id.analytic_id.id
            rec.account_analytic_id = account_analytic_id
