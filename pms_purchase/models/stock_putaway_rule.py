# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


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
    move_to_property = fields.Boolean(
        string="Move to Property Location",
        help="When enabled, incoming stock is routed to the property location "
        "linked on the purchase order line.",
    )
