# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import json

from odoo import _, fields, models
from odoo.tools import float_is_zero


class AccountMove(models.Model):
    _inherit = "account.move"

    # Field Declarations
    folio_ids = fields.Many2many(
        string="Folios",
        help="Folios where the account move are included",
        comodel_name="pms.folio",
        compute="_compute_folio_origin",
        relation="account_move_folio_ids_rel",
        column1="account_move_id",
        column2="folio_ids_id",
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Property with access to the element",
        comodel_name="pms.property",
    )
    outstanding_folios_debits_widget = fields.Text(
        compute="_compute_get_outstanding_folios_JSON"
    )
    has_folios_outstanding = fields.Boolean(
        compute="_compute_get_outstanding_folios_JSON"
    )

    def _compute_folio_origin(self):
        for inv in self:
            inv.folio_ids = False
            folios = inv.mapped("invoice_line_ids.folio_ids")
            if folios:
                inv.folio_ids = [(6, 0, folios.ids)]

    def _compute_get_outstanding_folios_JSON(self):
        self.ensure_one()
        self.outstanding_folios_debits_widget = json.dumps(False)
        if self.from_folio:
            payment_ids = self.folio_ids.mapped("payment_ids.id")
            if self.state == "open":
                account_partner = (
                    self.env["res.partner"]._find_accounting_partner(self.partner_id).id
                )
                domain = [
                    ("account_id", "=", self.account_id.id),
                    ("partner_id", "!=", account_partner),
                    ("reconciled", "=", False),
                    ("payment_id", "in", payment_ids),
                    "|",
                    "&",
                    ("amount_residual_currency", "!=", 0.0),
                    ("currency_id", "!=", None),
                    "&",
                    ("amount_residual_currency", "=", 0.0),
                    "&",
                    ("currency_id", "=", None),
                    ("amount_residual", "!=", 0.0),
                ]
                if self.type in ("out_invoice", "in_refund"):
                    domain.extend([("credit", ">", 0), ("debit", "=", 0)])
                    type_payment = _("Outstanding credits in Folio")
                else:
                    domain.extend([("credit", "=", 0), ("debit", ">", 0)])
                    type_payment = _("Outstanding debits")
                info = {
                    "title": "",
                    "outstanding": True,
                    "content": [],
                    "move_id": self.id,
                }
                lines = self.env["account.move.line"].search(domain)
                currency_id = self.currency_id
                if len(lines) != 0:
                    for line in lines:
                        # get the outstanding residual value in inv. currency
                        if line.currency_id and line.currency_id == self.currency_id:
                            amount_to_show = abs(line.amount_residual_currency)
                        else:
                            amount_to_show = line.company_id.currency_id.with_context(
                                date=line.date
                            ).compute(abs(line.amount_residual), self.currency_id)
                        if float_is_zero(
                            amount_to_show, precision_rounding=self.currency_id.rounding
                        ):
                            continue
                        if line.ref:
                            title = "{} : {}".format(line.move_id.name, line.ref)
                        else:
                            title = line.move_id.name
                        info["content"].append(
                            {
                                "journal_name": line.ref or line.move_id.name,
                                "title": title,
                                "amount": amount_to_show,
                                "currency": currency_id.symbol,
                                "id": line.id,
                                "position": currency_id.position,
                                "digits": [69, self.currency_id.decimal_places],
                            }
                        )
                    info["title"] = type_payment
                    self.outstanding_folios_debits_widget = json.dumps(info)
                    self.has_folio_outstanding = True

    def action_folio_payments(self):
        self.ensure_one()
        sales = self.mapped("invoice_line_ids.sale_line_ids.order_id")
        folios = self.env["pms.folio"].search([("order_id.id", "in", sales.ids)])
        payments_obj = self.env["account.payment"]
        payments = payments_obj.search([("folio_id", "in", folios.ids)])
        payment_ids = payments.mapped("id")
        return {
            "name": _("Payments"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "account.payment",
            "target": "new",
            "type": "ir.actions.act_window",
            "domain": [("id", "in", payment_ids)],
        }
