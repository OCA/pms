# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Fields declaration
    # TODO: REVIEW why not a Many2one?
    folio_line_ids = fields.Many2many(
        string="Folio Lines",
        help="The folio lines in the account move lines",
        copy=True,
        comodel_name="folio.sale.line",
        relation="folio_sale_line_invoice_rel",
        column1="invoice_line_id",
        column2="sale_line_id",
    )
    folio_ids = fields.Many2many(
        comodel_name="pms.folio",
        string="Folios",
        compute="_compute_folio_ids",
        store=True,
    )
    name_changed_by_user = fields.Boolean(
        string="Custom label",
        readonly=False,
        default=False,
        store=True,
        compute="_compute_name_changed_by_user",
    )
    pms_property_id = fields.Many2one(
        name="Property",
        comodel_name="pms.property",
        related="move_id.pms_property_id",
        store=True,
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

    @api.depends(
        "folio_line_ids",
        "payment_id",
        "payment_id.folio_ids",
        "statement_line_id",
        "statement_line_id.folio_ids",
    )
    def _compute_folio_ids(self):
        if self.folio_line_ids:
            self.folio_ids = self.folio_line_ids.mapped("folio_id")
        elif self.payment_id:
            self.folio_ids = self.payment_id.folio_ids
        elif self.statement_line_id:
            self.folio_ids = self.statement_line_id.folio_ids
        else:
            self.folio_ids = False

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
