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
        for acquirer in values["acquirers"]:
            if (
                acquirer.pms_property_ids
                and invoice.pms_property_id.id not in acquirer.pms_property_ids.ids
            ):
                values["acquirers"] -= acquirer
        for pms in values["pms"]:
            if pms.acquirer_id not in values["acquirers"].ids:
                values["pms"] -= pms
        return values
