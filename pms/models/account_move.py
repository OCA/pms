# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError
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
        store=True,
    )
    outstanding_folios_debits_widget = fields.Text(
        compute="_compute_get_outstanding_folios_JSON"
    )
    has_folios_outstanding = fields.Boolean(
        compute="_compute_get_outstanding_folios_JSON"
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

    @api.depends("invoice_line_ids")
    def _compute_folio_origin(self):
        for move in self:
            move.folio_ids = False
            if move.invoice_line_ids:
                move.folio_ids = move.mapped("invoice_line_ids.folio_ids.id")
            elif move.line_ids and move.line_ids.sale_line_ids:
                move.folio_ids = move.mapped("line_ids.sale_line_ids.folio_id.id")

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
