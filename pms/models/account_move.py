# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError


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
        store=True,
        readonly=False,
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="The property associated to the account move",
        comodel_name="pms.property",
        compute="_compute_pms_property_id",
        store=True,
        readonly=False,
        check_pms_properties=True,
    )

    @api.depends("journal_id", "folio_ids")
    def _compute_pms_property_id(self):
        for move in self:
            if move.folio_ids:
                move.pms_property_id = move.folio_ids.mapped("pms_property_id")
            elif len(move.journal_id.mapped("pms_property_ids")) == 1:
                move.pms_property_id = move.journal_id.mapped("pms_property_ids")[0]
            else:
                move.pms_property_id = False

    @api.depends("line_ids", "line_ids.folio_ids")
    def _compute_folio_origin(self):
        for move in self:
            move.folio_ids = False
            move.folio_ids = move.mapped("line_ids.folio_ids.id")

    def _compute_payments_widget_to_reconcile_info(self):
        for move in self:
            if not move.line_ids.folio_line_ids:
                super(AccountMove, move)._compute_payments_widget_to_reconcile_info()
            else:
                move.invoice_outstanding_credits_debits_widget = json.dumps(False)
                move.invoice_has_outstanding = False

                if (
                    move.state != "posted"
                    or move.payment_state not in ("not_paid", "partial")
                    or not move.is_invoice(include_receipts=True)
                ):
                    continue

                pay_term_lines = move.line_ids.filtered(
                    lambda line: line.account_id.user_type_id.type
                    in ("receivable", "payable")
                )

                domain = [
                    ("account_id", "in", pay_term_lines.account_id.ids),
                    ("parent_state", "=", "posted"),
                    ("reconciled", "=", False),
                    "|",
                    ("amount_residual", "!=", 0.0),
                    ("amount_residual_currency", "!=", 0.0),
                    "|",
                    (
                        "folio_ids",
                        "in",
                        move.line_ids.mapped("folio_line_ids.folio_id.id"),
                    ),
                    ("partner_id", "=", move.commercial_partner_id.id),
                ]

                payments_widget_vals = {
                    "outstanding": True,
                    "content": [],
                    "move_id": move.id,
                }

                if move.is_inbound():
                    domain.append(("balance", "<", 0.0))
                    payments_widget_vals["title"] = _("Outstanding credits")
                else:
                    domain.append(("balance", ">", 0.0))
                    payments_widget_vals["title"] = _("Outstanding debits")

                for line in self.env["account.move.line"].search(domain):

                    if line.currency_id == move.currency_id:
                        # Same foreign currency.
                        amount = abs(line.amount_residual_currency)
                    else:
                        # Different foreign currencies.
                        amount = move.company_currency_id._convert(
                            abs(line.amount_residual),
                            move.currency_id,
                            move.company_id,
                            line.date,
                        )

                    if move.currency_id.is_zero(amount):
                        continue

                    payments_widget_vals["content"].append(
                        {
                            "journal_name": line.ref or line.move_id.name,
                            "amount": amount,
                            "currency": move.currency_id.symbol,
                            "id": line.id,
                            "move_id": line.move_id.id,
                            "position": move.currency_id.position,
                            "digits": [69, move.currency_id.decimal_places],
                            "payment_date": fields.Date.to_string(line.date),
                        }
                    )

                if not payments_widget_vals["content"]:
                    continue

                move.invoice_outstanding_credits_debits_widget = json.dumps(
                    payments_widget_vals
                )
                move.invoice_has_outstanding = True

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

    def _search_default_journal(self, journal_types):
        """
        Search for the default journal based on the journal type and property,
        the parent method is overwritten to add the property filter if
        default_pms_property_id is set in context
        """
        journal = super(AccountMove, self)._search_default_journal(journal_types)
        if self._context.get("default_pms_property_id"):
            property_id = self._context.get("default_pms_property_id")
            pms_property = self.env["pms.property"].browse(property_id)
            domain = [
                ("company_id", "=", pms_property.company_id.id),
                ("type", "in", journal_types),
                ("pms_property_ids", "in", property_id),
            ]
            journal = self.env["account.journal"].search(domain, limit=1)
            if not journal:
                domain = [
                    ("company_id", "=", pms_property.company_id.id),
                    ("type", "in", journal_types),
                    ("pms_property_ids", "=", False),
                ]
                journal = self.env["account.journal"].search(domain, limit=1)
            if not journal:
                error_msg = _(
                    """No journal could be found in property %(property_name)s
                    for any of those types: %(journal_types)s""",
                    property_name=pms_property.display_name,
                    journal_types=", ".join(journal_types),
                )
                raise UserError(error_msg)
        return journal
