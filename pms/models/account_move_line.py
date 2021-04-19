# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Fields declaration
    # TODO: REVIEW why not a Many2one?
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
    name_changed_by_user = fields.Boolean(
        default=False,
        readonly=False,
        store=True,
        string="Custom label",
        compute="_compute_name_changed_by_user",
    )

    @api.depends("name")
    def _compute_name_changed_by_user(self):
        for record in self:
            # if not record._context.get("auto_name"):
            if not self._context.get("auto_name"):
                record.name_changed_by_user = True
            else:
                record.name_changed_by_user = False

    name = fields.Char(
        compute="_compute_name",
        store=True,
        readonly=False,
    )

    @api.depends("quantity")
    def _compute_name(self):
        for record in self:
            record.name = self.env["folio.sale.line"].generate_folio_sale_name(
                record.folio_line_ids.reservation_id,
                record.product_id,
                record.folio_line_ids.service_id,
                record.folio_line_ids.reservation_line_ids,
                record.folio_line_ids.service_line_ids,
                qty=record.quantity,
            )
            # TODO: check why this code doesn't work
            # if not record.name_changed_by_user:
            #   record.with_context(auto_name=True).name = self
            #       .env["folio.sale.line"].generate_folio_sale_name(
            #           record.folio_line_ids.service_id,
            #           record.folio_line_ids.reservation_line_ids,
            #           record.product_id,
            #           qty=record.quantity)
            #     record.with_context(auto_name=True)
            #       ._compute_name_changed_by_user()

    def _copy_data_extend_business_fields(self, values):
        super(AccountMoveLine, self)._copy_data_extend_business_fields(values)
        values["folio_line_ids"] = [(6, None, self.folio_line_ids.ids)]
