# Copyright 2022 Comunitea Servicios Tecnológicos S.L. (https://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountAsset(models.Model):
    _inherit = "account.asset"
    _check_pms_properties_auto = True

    pms_property_id = fields.Many2one(
        name="Property",
        comodel_name="pms.property",
        check_pms_properties=True,
    )

    @api.model
    def _xls_acquisition_fields(self):
        res = super()._xls_acquisition_fields()
        return res + ["pms_property_id"]

    @api.model
    def _xls_active_fields(self):
        res = super()._xls_active_fields()
        return res + ["pms_property_id"]

    @api.model
    def _xls_removal_fields(self):
        res = super()._xls_removal_fields()
        return res + ["pms_property_id"]
