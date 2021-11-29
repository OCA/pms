# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _compute_reservation_count(self):
        sale_orders_data = self.env["pms.reservation"].read_group(
            [("sale_order_id", "in", self.ids)], ["sale_order_id"], ["sale_order_id"]
        )
        reservation_count_data = {
            sale_order_data["sale_order_id"][0]: sale_order_data["sale_order_id_count"]
            for sale_order_data in sale_orders_data
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
        res = super(SaleOrder, self).action_confirm()
        for sale in self:
            reservation = self.env["pms.reservation"].search(
                [("sale_order_id", "=", sale.id)]
            )
            if reservation:
                reservation.action_book()
                # Set reservation confirm when payment is done by Generate a Payment Link
                if not sale.has_to_be_paid():
                    reservation.action_confirm()
        return res
