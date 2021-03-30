# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Fields declaration
    folio_line_ids = fields.Many2many(
        "folio.sale.line",
        "folio_sale_line_invoice_rel",
        "invoice_line_id",
        "sale_line_id",
        string="Folio Lines",
        copy=False,
    )
    folio_ids = fields.Many2many(
        "pms.folio",
        "payment_folio_rel",
        "move_id",
        "folio_id",
        string="Folios",
    )

    def _copy_data_extend_business_fields(self, values):
        super(AccountMoveLine, self)._copy_data_extend_business_fields(values)
        values["folio_line_ids"] = [(6, None, self.folio_line_ids.ids)]
