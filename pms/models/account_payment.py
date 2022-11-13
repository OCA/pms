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
        readonly=True,
    )
    origin_reference = fields.Char(
        string="Origin Reference",
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
                # If the payment is in a new invoice, we want it to be associated with all
                # folios of the invoice that don't are paid yet
                folio_ids = folios.filtered(lambda f: f.pending_amount > 0).ids
                rec.write({"folio_ids": [(6, 0, folio_ids)]})
            elif not rec.folio_ids:
                rec.folio_ids = False

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        line_vals_list = super(AccountPayment, self)._prepare_move_line_default_vals(
            write_off_line_vals
        )
        if self.folio_ids:
            for line in line_vals_list:
                line.update(
                    {
                        "folio_ids": [(6, 0, self.folio_ids.ids)],
                    }
                )
        return line_vals_list

    def _synchronize_to_moves(self, changed_fields):
        super(AccountPayment, self)._synchronize_to_moves(changed_fields)
        if "folio_ids" in changed_fields:
            for pay in self.with_context(skip_account_move_synchronization=True):
                pay.move_id.write(
                    {
                        "folio_ids": [(6, 0, pay.folio_ids.ids)],
                    }
                )

    # Business methods

    # def modify(self):
    #     self.cancel()
    #     vals = {
    #         "journal_id": self.journal_id,
    #         "partner_id": self.partner_id,
    #         "amount": self.amount,
    #         "payment_date": self.payment_date,
    #         "communication": self.communication,
    #         "state": "draft",
    #     }
    #     self.update(vals)
    #     self.with_context({"ignore_notification_post": True}).post()
    #     self._compute_folio_amount()
    #     if self.folio_id:
    #         msg = _("Payment %s modified: \n") % (self.communication)
    #         if self.save_amount and self.save_amount != self.amount:
    #             msg += _("Amount from %s to %s %s \n") % (
    #                 self.save_amount,
    #                 self.amount,
    #                 self.currency_id.symbol,
    #             )
    #         if self.save_date and self.save_date != self.payment_date:
    #             msg += _("Date from %s to %s \n") % (self.save_date, self.payment_date)
    #         if self.save_journal_id and self.save_journal_id != self.journal_id.id:
    #             msg += _("Journal from %s to %s") % (
    #                 self.env["account.journal"].browse(self.save_journal_id).name,
    #                 self.journal_id.name,
    #             )
    #         self.folio_id.message_post(subject=_("Payment"), body=msg)

    # def delete(self):
    #     msg = False
    #     if self.folio_id:
    #         msg = _("Deleted payment: %s %s ") % (self.amount, self.currency_id.symbol)
    #     self.cancel()
    #     self.move_name = ""
    #     self.unlink()
    #     if msg:
    #         self.folio_id.message_post(subject=_("Payment Deleted"), body=msg)

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        for payment in self:
            if (
                self.folio_ids
                and self.company_id.pms_invoice_downpayment_policy != "no"
                and not self.journal_id.avoid_autoinvoice_downpayment
            ):
                checkout_ref = max(self.folio_ids.mapped("last_checkout"))
                if (
                    self.company_id.pms_invoice_downpayment_policy == "all"
                    and payment.date < checkout_ref
                ) or (
                    self.company_id.pms_invoice_downpayment_policy
                    == "checkout_past_month"
                    and checkout_ref.month > payment.date.month
                    and checkout_ref.year >= payment.date.year
                ):
                    partner_id = (
                        payment.partner_id.id
                        or self.env.ref("pms.various_pms_partner").id
                    )
                    if payment.payment_type == "inbound":
                        invoice_wizard = self.env["folio.advance.payment.inv"].create(
                            {
                                "partner_invoice_id": partner_id,
                                "advance_payment_method": "fixed",
                                "fixed_amount": payment.amount,
                            }
                        )
                        move = invoice_wizard.with_context(
                            active_ids=self.folio_ids.ids,
                            return_invoices=True,
                        ).create_invoices()
                        move.action_post()
                        move_lines = move.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type
                            in ("receivable", "payable")
                        )
                        payment_lines = payment.move_id.line_ids.filtered(
                            lambda line: line.account_id == move_lines.account_id
                        )
                        if not move_lines.reconciled:
                            (payment_lines + move_lines).reconcile()
                    else:
                        # We try to revert the advance payment invoice
                        advance_invoices = self.env["account.move"].search(
                            [
                                ("folio_ids", "in", self.folio_ids.ids),
                                ("state", "=", "posted"),
                                ("payment_state", "=", "paid"),
                                ("move_type", "=", "out_invoice"),
                            ]
                        )
                        advance_invoices = advance_invoices.filtered(
                            lambda inv: any(
                                [
                                    line.folio_line_ids.is_downpayment
                                    for line in inv.invoice_line_ids
                                ]
                            )
                        )
                        if advance_invoices:
                            match_inv = advance_invoices.filtered(
                                lambda inv: round(inv.amount_total, 2)
                                == round(payment.amount, 2)
                            )
                            move_reversal = (
                                self.env["account.move.reversal"]
                                .with_context(
                                    active_model="account.move",
                                    active_ids=match_inv.ids
                                    if match_inv
                                    else advance_invoices.ids,
                                )
                                .create(
                                    {
                                        "date": fields.Date.today(),
                                        "reason": _("Deposit return"),
                                        "refund_method": "refund",
                                    }
                                )
                            )
                            move_reversal.reverse_moves()
                            move = move_reversal.new_move_ids
                            invoice_line = move.invoice_line_ids.filtered(
                                lambda l: not l.display_type
                            )
                            move.write(
                                {
                                    "invoice_line_ids": [
                                        (
                                            1,
                                            invoice_line.id,
                                            {
                                                "price_unit": payment.amount,
                                            },
                                        )
                                    ],
                                }
                            )
                            move_lines = move.line_ids.filtered(
                                lambda line: line.account_id.user_type_id.type
                                in ("receivable", "payable")
                            )
                            payment_lines = payment.move_id.line_ids.filtered(
                                lambda line: line.account_id == move_lines.account_id
                            )
                            move.sudo().action_post()
                            if not move_lines.reconciled:
                                (payment_lines + move_lines).reconcile()
        return res

    # def modify_payment(self):
    #     self.ensure_one()
    #     view_form_id = self.env.ref("pms.account_payment_view_form_folio").id
    #     # moves = self.mapped('move_ids.id')
    #     return {
    #         "name": _("Payment"),
    #         "view_type": "form",
    #         "views": [(view_form_id, "form")],
    #         "view_mode": "tree,form",
    #         "res_model": "account.payment",
    #         "target": "new",
    #         "init_mode": "edit",
    #         "type": "ir.actions.act_window",
    #         "res_id": self.id,
    #     }
