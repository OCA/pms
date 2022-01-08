# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.account.controllers.portal import PortalAccount


class PortalAccount(PortalAccount):
    def _invoice_get_page_view_values(self, invoice, access_token, **kwargs):
        """
        Override to add the pms property filter
        """
        values = super(PortalAccount, self)._invoice_get_page_view_values(
            invoice, access_token, **kwargs
        )
        acquirers = values.get("acquirers")
        for acquirer in acquirers:
            if (
                acquirer.pms_property_ids
                and invoice.pms_property_id.id not in acquirer.pms_property_ids.ids
            ):
                values["acquirers"] -= acquirer
        payment_tokens = values.get("payment_tokens")
        for pms in payment_tokens:
            if pms.acquirer_id not in values["acquirers"].ids:
                values["pms"] -= pms
        return values
