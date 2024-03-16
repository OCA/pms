from odoo import _, api, fields, models


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

    def render_folio_button(
        self, folio, submit_txt=None, render_values=None, custom_amount=None
    ):
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
                custom_amount or folio.pending_amount,
                folio.currency_id.id,
                values=values,
            )
        )

    @api.model
    def _compute_reference_prefix(self, values):
        res = super(PaymentTransaction, self)._compute_reference_prefix(values)
        if not res and values and values.get("folio_ids"):
            folios = self.new({"folio_ids": values["folio_ids"]}).folio_ids
            return "".join(folios.mapped("name"))[-9:]
        return None
