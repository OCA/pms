# Part of Odoo. See LICENSE file for full copyright and licensing details.

from werkzeug import urls

from odoo import models


class FolioPaymentLink(models.TransientModel):
    _inherit = "payment.link.wizard"
    _description = "Generate Sales Payment Link"

    # pylint: disable=W8110
    def _compute_link(self):
        """Override of the base method to add the folio_id in the link."""
        for payment_link in self:
            if payment_link.res_model == "pms.folio":
                # TODO: Review controller /website_payment/pay,
                # how inherit it to add acquirers by property?
                # now we send the first acquirer that has the property in pms_property_ids
                folio = self.env["pms.folio"].browse(payment_link.res_id)
                acquirer = self.env["payment.provider"].search(
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
                        "%s/payment/pay?reference=%s&amount=%s&currency_id=%s"
                        "&folio_id=%s&company_id=%s"
                        "&access_token=%s"
                    ) % (
                        record.get_base_url(),
                        urls.url_quote_plus(payment_link.description),
                        payment_link.amount,
                        payment_link.currency_id.id,
                        payment_link.res_id,
                        payment_link.company_id.id,
                        self._get_access_token(),
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
                super(FolioPaymentLink, payment_link)._compute_link()
