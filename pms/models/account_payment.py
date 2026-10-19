# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
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

    def _realign_move_lines_partner(self):
        """Keep the journal items of the payment aligned with its partner.

        Odoo only rewrites the journal items of a payment when the payment
        itself is written (_synchronize_to_moves), and the partner of a journal
        item is never recomputed from its move. So a payment whose partner was
        corrected by hand keeps its original partner on the journal items, and
        the partner ledger reports it under the wrong partner forever.
        """
        for payment in self:
            if not payment.partner_id:
                continue
            # partner_id is protected by the fiscal lock date: skip locked
            # entries instead of breaking the reconciliation for the user.
            lock_date = payment.company_id._get_user_fiscal_lock_date()
            if payment.move_id.date and payment.move_id.date <= lock_date:
                continue
            liquidity_lines, counterpart_lines, dummy = payment._seek_for_lines()
            partner = payment.partner_id
            lines = (liquidity_lines + counterpart_lines).filtered(
                lambda line, partner=partner: line.partner_id != partner
            )
            if lines:
                lines.write({"partner_id": partner.id})

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
