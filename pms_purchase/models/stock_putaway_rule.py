# Copyright (c) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPutawayRule(models.Model):
    _inherit = "stock.putaway.rule"

    location_out_id = fields.Many2one(
        "stock.location",
        "Store to",
        check_company=True,
        domain="[('id', 'child_of', location_in_id),"
        " ('id', '!=', location_in_id),"
        " '|',"
        " ('company_id', '=', False),"
        " ('company_id', '=', company_id)]",
        ondelete="cascade",
        required=False,
    )

    @api.model
    def _get_putaway_options(self):
        res = super()._get_putaway_options()
        res.append(("move_to_property", "Move to the location of the property"))
        return res
