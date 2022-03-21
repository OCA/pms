# Copyright (c) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        self.ensure_one()
        rules = self.location_dest_id.putaway_rule_ids.filtered(
            lambda x: x.product_id == self.product_id
        )
        if not rules:
            rules = self.location_dest_id.putaway_rule_ids.filtered(
                lambda x: x.category_id == self.product_id.categ_id
            )
        rules = rules and rules[0] or self.env["stock.putaway.rule"]
        res = super(StockMove, self)._prepare_move_line_vals(quantity, reserved_quant)
        po = self.picking_id.purchase_id
        po_warehouse_id = po.picking_type_id.default_location_dest_id.get_warehouse().id
        line = self.purchase_line_id
        property_warehouse_id = (
            line.pms_property_id.stock_location_id.get_warehouse().id
        )
        if (
            rules.method == "move_to_property"
            and line.pms_property_id
            and property_warehouse_id == po_warehouse_id
        ):
            res.update(
                {
                    "location_dest_id": line.pms_property_id.stock_location_id.id,
                }
            )
        return res
