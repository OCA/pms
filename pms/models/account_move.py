# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import itertools as it
import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"
    _check_pms_properties_auto = True

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
        # check_pms_properties=True,
    )
    # journal_id = fields.Many2one(check_pms_properties=True)
    is_simplified_invoice = fields.Boolean(
        help="Technical field to know if the invoice is simplified",
        related="journal_id.is_simplified_invoice",
        store=True,
    )
    origin_agency_id = fields.Many2one(
        string="Origin Agency",
        help="The agency where the folio account move originates",
        comodel_name="res.partner",
        domain="[('is_agency', '=', True)]",
        compute="_compute_origin_agency_id",
        store=True,
        readonly=False,
    )

    @api.onchange("pms_property_id")
    def _onchange_pms_property_id(self):
        for move in self:
            journals = self.env["account.journal"].search(
                [
                    ("pms_property_ids", "=", move.pms_property_id.id),
                ]
            )
            if journals:
                move.journal_id = journals[0]
            else:
                move.journal_id = False

    @api.depends("journal_id", "folio_ids")
    def _compute_pms_property_id(self):
        for move in self:
            if move.folio_ids:
                move.pms_property_id = move.folio_ids.mapped("pms_property_id")
            elif len(move.journal_id.mapped("pms_property_ids")) == 1:
                move.pms_property_id = move.journal_id.mapped("pms_property_ids")[0]
            elif not move.journal_id.pms_property_ids:
                move.pms_property_id = False
            elif not move.pms_property_id:
                move.pms_property_id = False

    @api.depends("line_ids", "line_ids.folio_ids")
    def _compute_folio_origin(self):
        for move in self:
            move.folio_ids = False
            move.folio_ids = move.mapped("line_ids.folio_ids.id")

    @api.depends("line_ids", "line_ids.origin_agency_id")
    def _compute_origin_agency_id(self):
        """
        Compute the origin agency of the account move
        if the move has multiple agencies in origin,
        the first one is returned (REVIEW: is this correct?)
        """
        self.origin_agency_id = False
        for move in self:
            agencies = move.mapped("line_ids.origin_agency_id")
            if agencies:
                move.origin_agency_id = agencies[0]

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

                payments_widget_vals = {
                    "outstanding": True,
                    "content": [],
                    "move_id": move.id,
                }

                if move.is_inbound():
                    domain = [("balance", "<", 0.0)]
                    payments_widget_vals["title"] = _("Outstanding credits")
                else:
                    domain = [("balance", ">", 0.0)]
                    payments_widget_vals["title"] = _("Outstanding debits")

                domain.extend(
                    [
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
                )

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

    def _search_default_journal(self, journal_types):
        """
        Search for the default journal based on the journal type and property,
        the parent method is overwritten to add the property filter if
        default_pms_property_id is set in context
        """
        journal = super(AccountMove, self)._search_default_journal(journal_types)
        company_id = self._context.get("default_company_id", self.env.company.id)
        company = self.env["res.company"].browse(company_id)
        pms_property_id = self.env.context.get(
            "default_pms_property_id", self.pms_property_id.id
        ) or (
            self.env.user.get_active_property_ids()
            and self.env.user.get_active_property_ids()[0]
        )
        pms_property = self.env["pms.property"].browse(pms_property_id)
        if pms_property:
            domain = [
                ("company_id", "=", pms_property.company_id.id),
                ("type", "in", journal_types),
                ("pms_property_ids", "in", pms_property.id),
            ]
            journal = self.env["account.journal"].search(domain, limit=1)
            if not journal:
                domain = [
                    ("company_id", "=", pms_property.company_id.id),
                    ("type", "in", journal_types),
                    ("pms_property_ids", "=", False),
                ]
                journal = self.env["account.journal"].search(domain, limit=1)
        else:
            domain = [
                ("company_id", "=", company_id),
                ("type", "in", journal_types),
                ("pms_property_ids", "=", False),
            ]
            journal = self.env["account.journal"].search(domain, limit=1)
        if not journal:
            if pms_property:
                error_msg = _(
                    """No journal could be found in property %(property_name)s
                    for any of those types: %(journal_types)s""",
                    property_name=pms_property.display_name,
                    journal_types=", ".join(journal_types),
                )
            else:
                error_msg = _(
                    """No journal could be found in company %(company_name)s
                    for any of those types: %(journal_types)s""",
                    company_name=company.display_name,
                    journal_types=", ".join(journal_types),
                )
            raise UserError(error_msg)
        return journal

    @api.depends("pms_property_id")
    def _compute_suitable_journal_ids(self):
        super(AccountMove, self)._compute_suitable_journal_ids()
        for move in self:
            if move.pms_property_id:
                move.suitable_journal_ids = move.suitable_journal_ids.filtered(
                    lambda j: not j.pms_property_ids
                    or move.pms_property_id.id in j.pms_property_ids.ids
                )

    def _autoreconcile_folio_payments(self):
        """
        Reconcile payments with the invoice
        """
        # TODO: Add setting option to enable automatic payment reconciliation
        for move in self.filtered(lambda m: m.state == "posted"):
            if move.is_invoice(include_receipts=True) and move.folio_ids:
                to_reconcile_payments_widget_vals = json.loads(
                    move.invoice_outstanding_credits_debits_widget
                )
                if not to_reconcile_payments_widget_vals:
                    continue
                current_amounts = {
                    vals["move_id"]: vals["amount"]
                    for vals in to_reconcile_payments_widget_vals["content"]
                }
                pay_term_lines = move.line_ids.filtered(
                    lambda line: line.account_id.user_type_id.type
                    in ("receivable", "payable")
                )
                to_propose = (
                    self.env["account.move"]
                    .browse(list(current_amounts.keys()))
                    .line_ids.filtered(
                        lambda line: line.account_id == pay_term_lines.account_id
                        and line.folio_ids in move.folio_ids
                        and (
                            line.move_id.partner_id == move.partner_id
                            or not line.move_id.partner_id
                        )
                    )
                )
                to_reconcile = self.match_pays_by_amount(
                    payments=to_propose, invoice=move
                )
                if to_reconcile:
                    (pay_term_lines + to_reconcile).reconcile()
                    # Set partner in payment
                    for record in to_reconcile:
                        if record.payment_id and not record.payment_id.partner_id:
                            record.payment_id.partner_id = move.partner_id
                        if (
                            record.statement_line_id
                            and not record.statement_line_id.partner_id
                        ):
                            record.statement_line_id.partner_id = move.partner_id
        return True

    def _post(self, soft=True):
        """
        Overwrite the original method to add the folio_ids to the invoice
        """
        for record in self:
            record._check_pms_valid_invoice(record)
        res = super(AccountMove, self)._post(soft)
        self._autoreconcile_folio_payments()
        return res

    def match_pays_by_amount(self, payments, invoice):
        """
        Match payments by amount
        """
        for i in range(len(payments)):
            combinations = list(it.combinations(payments, i + 1))
            for combi in combinations:
                # TODO: compare with currency differences
                if sum(abs(item.balance) for item in combi) == invoice.amount_residual:
                    return payments.filtered(
                        lambda p: p.id in [item.id for item in combi]
                    )
        return []

    @api.model
    def _check_pms_valid_invoice(self, move):
        """
        Check invoice and receipts legal status
        """
        if (
            move.company_id.check_min_partner_data_invoice
            and move.is_invoice(include_receipts=True)
            and not move.journal_id.is_simplified_invoice
            and (
                not move.partner_id or not move.partner_id._check_enought_invoice_data()
            )
        ):
            raise UserError(
                _(
                    "You cannot validate this invoice. Please check the "
                    " partner has the complete information required."
                )
            )
        if move.journal_id.is_simplified_invoice:
            move._check_simplified_restrictions()
        return True

    def _check_simplified_restrictions(self):
        self.ensure_one()
        if (
            self.pms_property_id
            and self.amount_total > self.pms_property_id.max_amount_simplified_invoice
            and (
                not self.pms_property_id.avoid_simplified_max_amount_downpayment
                or not self._is_downpayment()
            )
        ):
            mens = _(
                "The total amount of the simplified invoice is higher than the "
                "maximum amount allowed for simplified invoices."
            )
            if self.folio_ids:
                self.folio_ids.message_post(body=mens)
            raise ValidationError(mens)
        return True

    def _proforma_access_url(self):
        self.ensure_one()
        if self.is_invoice(include_receipts=True):
            return "/my/invoices/proforma/%s" % (self.id)
        else:
            return False

    def get_proforma_portal_url(
        self,
        suffix=None,
        report_type=None,
        download=None,
        query_string=None,
        anchor=None,
    ):
        """
        Get a proforma portal url for this model, including access_token.
        The associated route must handle the flags for them to have any effect.
        - suffix: string to append to the url, before the query string
        - report_type: report_type query string, often one of: html, pdf, text
        - download: set the download query string to true
        - query_string: additional query string
        - anchor: string to append after the anchor #
        """
        self.ensure_one()
        url = self._proforma_access_url() + "%s?access_token=%s%s%s%s%s" % (
            suffix if suffix else "",
            self._portal_ensure_token(),
            "&report_type=%s" % report_type if report_type else "",
            "&download=true" if download else "",
            query_string if query_string else "",
            "#%s" % anchor if anchor else "",
        )
        return url
