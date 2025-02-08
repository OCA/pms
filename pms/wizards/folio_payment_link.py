# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class FolioPaymentLink(models.TransientModel):
    _inherit = "payment.link.wizard"
    _description = "Generate Folio Payment Link"

    def _get_payment_provider_available(self, res_model, res_id, **kwargs):
        """Select and return the providers matching the criteria.

        :param str res_model: active model
        :param int res_id: id of 'active_model' record
        :return: The compatible providers
        :rtype: recordset of `payment.provider`
        """
        # If the model has the field "pms_property_id",
        # we will use it to filter the providers
        record = self.env[res_model].browse(res_id)
        if hasattr(record, "pms_property_id"):
            kwargs["pms_property_id"] = record.pms_property_id.id
        if res_model == "pms.folio":
            kwargs["pms_folio_id"] = res_id
        return super()._get_payment_provider_available(res_model, res_id, **kwargs)

    def _get_additional_link_values(self):
        """Override of `payment` to add `pms_folio_id` and "pms_property_id"
        to the payment link values.

        Note: self.ensure_one()

        :return: The additional payment link values.
        :rtype: dict
        """
        res = super()._get_additional_link_values()
        if self.res_model != "pms.folio":
            return res

        # If target record has pms_property_id
        # add pms_property_id to link
        folio_res = {}
        record = self.env[self.res_model].browse(self.res_id)
        if hasattr(record, "pms_property_id"):
            folio_res["pms_property_id"] = record.pms_property_id.id

        if self.res_model == "pms.folio":
            folio_res["pms_folio_id"] = self.res_id

        return folio_res
