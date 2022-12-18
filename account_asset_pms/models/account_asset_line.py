# Copyright 2022 Comunitea Servicios Tecnológicos S.L. (https://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountAssetLine(models.Model):
    _inherit = "account.asset.line"

    def create_move(self):
        return super(
            AccountAssetLine,
            self.with_context(force_pms_property=self.asset_id.pms_property_id.id),
        ).create_move()
