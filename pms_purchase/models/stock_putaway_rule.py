# Copyright (c) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class StockPutawayRule(models.Model):
    _inherit = "stock.putaway.rule"

    @api.model
    def _get_putaway_options(self):
        res = super()._get_putaway_options()
        res.append(("move_to_property", "Move to the location of the property"))
        return res
