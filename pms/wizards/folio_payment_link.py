# Part of Odoo. See LICENSE file for full copyright and licensing details.

from werkzeug import urls

from odoo import api, models


class FolioPaymentLink(models.TransientModel):
    _inherit = "payment.link.wizard"
    _description = "Generate Sales Payment Link"

    @api.model
    def default_get(self, fields):
        res = super(FolioPaymentLink, self).default_get(fields)
        if res["res_id"] and res["res_model"] == "pms.folio":
            record = self.env[res["res_model"]].browse(res["res_id"])
            res.update(
                {
                    "description": record.name,
                    "amount": record.pending_amount,
                    "currency_id": record.currency_id.id,
                    "partner_id": record.partner_id.id if record.partner_id else False,
                    "amount_max": record.pending_amount,
                }
            )
        return res

    def _generate_link(self):
        """Override of the base method to add the folio_id in the link."""
        for payment_link in self:
            if payment_link.res_model == "pms.folio":
                # TODO: Review controller /website_payment/pay,
                # how inherit it to add acquirers by property?
                # now we send the first acquirer that has the property in pms_property_ids
                folio = self.env["pms.folio"].browse(payment_link.res_id)
                acquirer = self.env["payment.acquirer"].search(
                    [
                        ("pms_property_ids", "in", folio.pms_property_id.id),
                        ("state", "=", "enabled"),
                    ],
                    limit=1,
                )
                if acquirer:
                    record = self.env[payment_link.res_model].browse(
                        payment_link.res_id
                    )
                    payment_link.link = (
                        "%s/website_payment/pay?reference=%s&amount=%s&currency_id=%s"
                        "&folio_id=%s&company_id=%s"
                        "&access_token=%s"
                    ) % (
                        record.get_base_url(),
                        urls.url_quote_plus(payment_link.description),
                        payment_link.amount,
                        payment_link.currency_id.id,
                        payment_link.res_id,
                        payment_link.company_id.id,
                        payment_link.access_token,
                    )
                    if acquirer:
                        payment_link.link += "&acquirer_id=%s" % acquirer.id
                    if payment_link.partner_id:
                        payment_link.link += (
                            "&partner_id=%s" % payment_link.partner_id.id
                        )
                    if not acquirer or acquirer.state != "enabled":
                        payment_link.link = False
                else:
                    payment_link.link = False
            else:
                super(FolioPaymentLink, payment_link)._generate_link()
