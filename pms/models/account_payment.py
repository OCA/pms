# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    # Fields declaration
    folio_id = fields.Many2one(
        string="Folio Reference",
        help="Folio in account payment",
        comodel_name="pms.folio",
    )

    # Business methods

    def modify(self):
        self.cancel()
        vals = {
            "journal_id": self.journal_id,
            "partner_id": self.partner_id,
            "amount": self.amount,
            "payment_date": self.payment_date,
            "communication": self.communication,
            "state": "draft",
        }
        self.update(vals)
        self.with_context({"ignore_notification_post": True}).post()
        self._compute_folio_amount()
        if self.folio_id:
            msg = _("Payment %s modified: \n") % (self.communication)
            if self.save_amount and self.save_amount != self.amount:
                msg += _("Amount from %s to %s %s \n") % (
                    self.save_amount,
                    self.amount,
                    self.currency_id.symbol,
                )
            if self.save_date and self.save_date != self.payment_date:
                msg += _("Date from %s to %s \n") % (self.save_date, self.payment_date)
            if self.save_journal_id and self.save_journal_id != self.journal_id.id:
                msg += _("Journal from %s to %s") % (
                    self.env["account.journal"].browse(self.save_journal_id).name,
                    self.journal_id.name,
                )
            self.folio_id.message_post(subject=_("Payment"), body=msg)

    def delete(self):
        msg = False
        if self.folio_id:
            msg = _("Deleted payment: %s %s ") % (self.amount, self.currency_id.symbol)
        self.cancel()
        self.move_name = ""
        self.unlink()
        if msg:
            self.folio_id.message_post(subject=_("Payment Deleted"), body=msg)

    def post(self):
        rec = super(AccountPayment, self).post()
        if rec and not self._context.get("ignore_notification_post", False):
            for pay in self:
                if pay.folio_id:
                    msg = _(
                        "Payment of %s %s registered from %s \
                            using %s payment method"
                    ) % (
                        pay.amount,
                        pay.currency_id.symbol,
                        pay.communication,
                        pay.journal_id.name,
                    )
                    pay.folio_id.message_post(subject=_("Payment"), body=msg)

    def modify_payment(self):
        self.ensure_one()
        view_form_id = self.env.ref("pms.account_payment_view_form_folio").id
        # moves = self.mapped('move_ids.id')
        return {
            "name": _("Payment"),
            "view_type": "form",
            "views": [(view_form_id, "form")],
            "view_mode": "tree,form",
            "res_model": "account.payment",
            "target": "new",
            "init_mode": "edit",
            "type": "ir.actions.act_window",
            "res_id": self.id,
        }
