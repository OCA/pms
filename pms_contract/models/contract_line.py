# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# Copyright (c) 2021 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ContractLine(models.Model):
    _inherit = "contract.line"

    property_id = fields.Many2one(
        "pms.property",
        string="Property",
    )

    def _prepare_invoice_line(self, **kwargs):
        invoice_line_vals = super()._prepare_invoice_line(**kwargs)
        if self.property_id:
            invoice_line_vals.update({"property_ids": [(6, 0, self.property_id.ids)]})
        return invoice_line_vals
