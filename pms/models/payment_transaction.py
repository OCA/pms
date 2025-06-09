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
    folio_ids_nbr = fields.Integer(
        compute="_compute_folio_ids_nbr", string="# of Folios"
    )

    def _create_payment(self):
        self.ensure_one()
        return super()._create_payment(folio_ids=self.folio_ids)

    def render_folio_button(
        self, folio, submit_txt=None, render_values=None, custom_amount=None
    ):
        values = {
            "partner_id": (
                folio.partner_id.id or self.env.ref("pms.various_pms_partner").id
            ),
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
    def _compute_reference_prefix(self, provider_code, separator, **values):
        if provider_code == "redsys" and "reference" in values:
            values["reference"] = values["reference"][-8:]
        reference = super()._compute_reference_prefix(
            provider_code, separator=separator, **values
        )
        return reference

    @api.depends("folio_ids")
    def _compute_folio_ids_nbr(self):
        for trans in self:
            trans.folio_ids_nbr = len(trans.folio_ids)

    def action_view_folios(self):
        action = {
            "name": _("Folio(s)"),
            "type": "ir.actions.act_window",
            "res_model": "pms.folio",
            "target": "current",
        }
        folio_ids = self.folio_ids.ids
        if len(folio_ids) == 1:
            action["res_id"] = folio_ids[0]
            action["view_mode"] = "form"
        else:
            action["view_mode"] = "tree,form"
            action["domain"] = [("id", "in", folio_ids)]
        return action
