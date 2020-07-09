# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PmsBoardServiceLine(models.Model):
    _name = "pms.board.service.line"
    _description = "Services on Board Service included"

    # Default methods
    def _get_default_price(self):
        if self.product_id:
            return self.product_id.list_price

    # Fields declaration
    pms_board_service_id = fields.Many2one(
        "pms.board.service", "Board Service", ondelete="cascade", required=True
    )
    product_id = fields.Many2one("product.product", string="Product", required=True)
    pms_property_ids = fields.Many2many(
        "pms.property", related="pms_board_service_id.pms_property_ids"
    )
    amount = fields.Float(
        "Amount", digits=("Product Price"), default=_get_default_price
    )

    # Constraints and onchanges
    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            self.update({"amount": self.product_id.list_price})
