# Copyright 2022 Comunitea Servicios Tecnológicos S.L. (https://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _prepare_asset_vals(self, aml):
        res = super()._prepare_asset_vals(aml)
        res.update({"pms_property_id": aml.pms_property_id or self.pms_property_id})
        return res
