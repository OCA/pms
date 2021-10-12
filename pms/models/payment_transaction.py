from odoo import fields, models


class PaymentTransaction(models.Model):
    _name = "payment.transaction"

    folio_ids = fields.Many2many(
        string="Folios",
        comodel_name="pms.folio",
        ondelete="cascade",
        relation="account_bank_statement_folio_rel",
        column1="account_journal_id",
        column2="folio_id",
    )

    def _create_payment(self, add_payment_vals=False):
        self.ensure_one()
        if not add_payment_vals:
            add_payment_vals = {}
        if self.folio_ids:
            add_payment_vals["folio_ids"] = [(6, 0, self.folio_ids.ids)]
        return super(PaymentTransaction, self)._create_payment(add_payment_vals)
