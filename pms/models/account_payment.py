# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from collections import defaultdict

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    folio_ids = fields.Many2many(
        string="Folios",
        comodel_name="pms.folio",
        compute="_compute_folio_ids",
        store=True,
        readonly=False,
        relation="account_payment_folio_rel",
        column1="payment_id",
        column2="folio_id",
    )
    origin_agency_id = fields.Many2one(
        string="Origin Agency",
        help="The agency where the folio account move originates",
        comodel_name="res.partner",
        domain="[('is_agency', '=', True)]",
        compute="_compute_origin_agency_id",
        store=True,
        index=True,
        readonly=True,
    )
    origin_reference = fields.Char(
        help="The reference of the payment origin",
    )

    @api.depends("reconciled_invoice_ids", "reconciled_bill_ids")
    def _compute_origin_agency_id(self):
        """
        Compute the origin agency of the sale line,
        if the line has multiple agencies in origin,
        (p.e. nights with different agencies in origin),
        the first one is returned (REVIEW: is this correct?)
        """
        for rec in self:
            inv_agency_ids = rec.reconciled_invoice_ids.mapped(
                "line_ids.folio_line_ids.origin_agency_id.id"
            )
            bill_agency_ids = rec.reconciled_bill_ids.mapped(
                "line_ids.folio_line_ids.origin_agency_id.id"
            )
            agency_ids = list(set(inv_agency_ids + bill_agency_ids))
            if agency_ids:
                rec.write({"origin_agency_id": agency_ids[0]})
            elif (
                not rec.reconciled_invoice_ids
                and not rec.reconciled_bill_ids
                and rec.folio_ids
            ):
                rec.origin_agency_id = rec.origin_agency_id
            else:
                rec.origin_agency_id = False

    @api.depends("reconciled_invoice_ids", "reconciled_bill_ids")
    def _compute_folio_ids(self):
        for rec in self:
            inv_folio_ids = rec.reconciled_invoice_ids.mapped(
                "line_ids.folio_line_ids.folio_id.id"
            )
            bill_folio_ids = rec.reconciled_bill_ids.mapped(
                "line_ids.folio_line_ids.folio_id.id"
            )
            folio_ids = list(set(inv_folio_ids + bill_folio_ids))
            # If the payment was already assigned to a specific page of the invoice,
            # we do not want it to be associated with others
            if folio_ids and len(set(rec.folio_ids.ids) & set(folio_ids)) == 0:
                folios = self.env["pms.folio"].browse(folio_ids)
                # If the payment is in a new invoice, we want it to be
                # associated with all folios of the invoice
                # that don't are paid yet
                folio_ids = folios.filtered(lambda f: f.pending_amount > 0).ids
                rec.write({"folio_ids": [(6, 0, folio_ids)]})
            elif not rec.folio_ids:
                rec.folio_ids = False

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        line_vals_list = super()._prepare_move_line_default_vals(write_off_line_vals)
        if self.folio_ids:
            for line in line_vals_list:
                line.update(
                    {
                        "folio_ids": [(6, 0, self.folio_ids.ids)],
                    }
                )
        return line_vals_list

    # pylint: disable=W8110
    def _synchronize_to_moves(self, changed_fields):
        super()._synchronize_to_moves(changed_fields)
        if "folio_ids" in changed_fields:
            for pay in self.with_context(skip_account_move_synchronization=True):
                pay.move_id.write(
                    {
                        "folio_ids": [(6, 0, pay.folio_ids.ids)],
                    }
                )

    def action_draft(self):
        for payment in self:
            if payment._check_has_downpayment_invoice(payment):
                downpayment_invoices = payment.reconciled_invoice_ids.filtered(
                    lambda inv: inv._is_downpayment()
                )
                if downpayment_invoices.state == "posted":
                    default_values_list = [
                        {
                            "ref": _(f'Reversal of: {move.name + " - " + move.ref}'),
                        }
                        for move in downpayment_invoices
                    ]
                    downpayment_invoices._reverse_moves(
                        default_values_list, cancel=True
                    )
                else:
                    downpayment_invoices.unlink()
        return super().action_draft()

    @api.model
    def auto_invoice_downpayments(self, offset=0):
        """
        This method is called by a cron job to invoice the downpayments
        based on the company settings.
        """
        date_reference = fields.Date.today() - relativedelta(days=offset)
        payments = self._get_downpayments_to_invoice(date_reference)
        for payment in payments:
            partner_id = (
                payment.partner_id.id or self.env.ref("pms.various_pms_partner").id
            )
            self._create_downpayment_invoice(
                payment=payment,
                partner_id=partner_id,
            )
        return True

    @api.model
    def _get_downpayments_to_invoice(self, date_reference):
        companys = self.env["res.company"].search([])
        payments = self.env["account.payment"]
        for company in companys:
            if company.pms_invoice_downpayment_policy == "all":
                date_ref = fields.Date.today()
            elif company.pms_invoice_downpayment_policy == "checkout_past_month":
                date_ref = fields.Date.today().replace(
                    day=1, month=fields.Date.today().month + 1
                )
            else:
                continue
            payments += self.search(
                [
                    ("state", "=", "posted"),
                    ("partner_type", "=", "customer"),
                    ("company_id", "=", company.id),
                    ("journal_id.avoid_autoinvoice_downpayment", "=", False),
                    ("folio_ids", "!=", False),
                    ("folio_ids.last_checkout", ">=", date_ref),
                    ("date", "<=", date_reference),
                ]
            )
        payments = payments.filtered(lambda p: not p.reconciled_invoice_ids)
        return payments

    @api.model
    def _check_has_downpayment_invoice(self, payment):
        if (
            payment.folio_ids
            and payment.partner_type == "customer"
            and payment.reconciled_invoice_ids.filtered(
                lambda inv: inv._is_downpayment()
            )
        ):
            return True
        return False

    @api.model
    def _create_downpayment_invoice(self, payment, partner_id):
        invoice_wizard = self.env["folio.advance.payment.inv"].create(
            {
                "partner_invoice_id": partner_id,
                "advance_payment_method": "fixed",
                "fixed_amount": payment.amount,
            }
        )
        move = invoice_wizard.with_context(
            active_ids=payment.folio_ids.ids,
            return_invoices=True,
        ).create_invoices()
        if payment.payment_type == "outbound":
            move.action_switch_invoice_into_refund_credit_note()
        move.action_post()
        for invoice, payment_move in zip(move, payment.move_id, strict=True):
            group = defaultdict(list)
            for line in (invoice.line_ids + payment_move.line_ids).filtered(
                lambda r: not r.reconciled
            ):
                group[(line.account_id, line.currency_id)].append(line.id)
            for (account, _dummy), line_ids in group.items():
                if (
                    account.reconcile or account.account_type == "liquidity"
                ):  # TODO: liquidity not in account.account_type
                    self.env["account.move.line"].browse(line_ids).reconcile()
        # Set folio sale lines default_invoice_to to partner downpayment invoice
        for folio in payment.folio_ids:
            for sale_line in folio.sale_line_ids.filtered(
                lambda r: not r.default_invoice_to
            ):
                sale_line.default_invoice_to = move.partner_id.id

        return move
