# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    folio_ids = fields.Many2many(
        string="Folios",
        comodel_name="pms.folio",
        ondelete="cascade",
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
            if folio_ids:
                rec.write({"folio_ids": [(6, 0, folio_ids)]})
            elif (
                not rec.reconciled_invoice_ids
                and not rec.reconciled_bill_ids
                and rec.folio_ids
            ):
                rec.folio_ids = rec.folio_ids
            else:
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

    # def post(self):
    #     rec = super(AccountPayment, self).post()
    #     if rec and not self._context.get("ignore_notification_post", False):
    #         for pay in self:
    #             if pay.folio_id:
    #                 msg = _(
    #                     "Payment of %s %s registered from %s \
    #                         using %s payment method"
    #                 ) % (
    #                     pay.amount,
    #                     pay.currency_id.symbol,
    #                     pay.communication,
    #                     pay.journal_id.name,
    #                 )
    #                 pay.folio_id.message_post(subject=_("Payment"), body=msg)

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
