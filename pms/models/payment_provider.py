# Copyright 2025 Darío Lodeiros <dario@roomdoo.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PaymentAcquirer(models.Model):
    _inherit = "payment.provider"
    _check_pms_properties_auto = True

    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        required=False,
        comodel_name="pms.property",
        relation="pms_acquirer_property_rel",
        column1="acquirer_id",
        column2="property_id",
        check_pms_properties=True,
    )

    @api.model
    def _get_compatible_providers(self, *args, pms_property_id=None, **kwargs):
        """Override of payment to filter the providers based on the property.

        :param int pms_property_id: The provided property, as a `pms.property` id
        :return: The compatible providers
        :rtype: recordset of `payment.provider`
        """
        compatible_providers = super()._get_compatible_providers(
            *args, pms_property_id=pms_property_id, **kwargs
        )
        if pms_property_id:
            pms_property_id = int(pms_property_id)
            compatible_providers = compatible_providers.filtered(
                lambda acquirer: not acquirer.pms_property_ids
                or pms_property_id in acquirer.pms_property_ids.ids
            )
        return compatible_providers
