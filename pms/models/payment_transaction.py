from odoo import _, fields, models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"
    _check_pms_properties_auto = True

    folio_ids = fields.Many2many(
        string="Folios",
        comodel_name="pms.folio",
        ondelete="cascade",
        relation="payment_transaction_folio_rel",
        column1="payment_transaction_id",
        column2="folio_id",
    )

    def _create_payment(self, add_payment_vals=False):
        self.ensure_one()
        if not add_payment_vals:
            add_payment_vals = {}
        if self.folio_ids:
            add_payment_vals["folio_ids"] = [(6, 0, self.folio_ids.ids)]
        return super(PaymentTransaction, self)._create_payment(add_payment_vals)

    def render_folio_button(self, folio, submit_txt=None, render_values=None):
        self.reference = folio.name
        values = {
            "partner_id": folio.partner_id.id,
            "type": self.type,
        }
        if render_values:
            values.update(render_values)
        return (
            self.acquirer_id.with_context(
                submit_class="btn btn-primary", submit_txt=submit_txt or _("Pay Now")
            )
            .sudo()
            .render(
                self.reference,
                folio.pending_amount,
                folio.currency_id.id,
                values=values,
            )
        )
