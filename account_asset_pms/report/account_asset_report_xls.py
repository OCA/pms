# Copyright 2022 Comunitea Servicios Tecnológicos S.L. (https://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AssetReportXlsx(models.AbstractModel):
    _inherit = "report.account_asset_management.asset_report_xls"

    def _get_asset_template(self):
        asset_template = super()._get_asset_template()
        asset_template.update(
            {
                "pms_property": {
                    "header": {"type": "string", "value": self._("PMS Property")},
                    "asset": {
                        "type": "string",
                        "value": self._render(
                            "asset.pms_property_id.display_name or ''"
                        ),
                    },
                    "width": 20,
                }
            }
        )
        return asset_template
