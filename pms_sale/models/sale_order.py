# Copyright (c) 2021 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _compute_reservation_count(self):
        reservation_count_data = {
            sale_order.id: count
            for sale_order, count in self.env["pms.reservation"]._read_group(
                [("sale_order_id", "in", self.ids)],
                ["sale_order_id"],
                ["__count"],
            )
        }
        for sale_order in self:
            sale_order.reservation_count = reservation_count_data.get(sale_order.id, 0)

    reservation_count = fields.Integer(
        "Reservations Count", compute="_compute_reservation_count"
    )

    def action_view_reservation_list(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "pms_sale.action_pms_reservation"
        )
        action["domain"] = [("sale_order_id", "in", self.ids)]
        return action

    def action_confirm(self):
        res = super().action_confirm()
        for sale in self:
            reservation = self.env["pms.reservation"].search(
                [("sale_order_id", "=", sale.id)]
            )
            if reservation:
                reservation.action_book()
                # Set reservation confirm when payment is done by payment link
                if not sale._has_to_be_paid():
                    reservation.action_confirm()
        return res
