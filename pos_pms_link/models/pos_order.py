##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2022 Comunitea Servicios Tecnológicos S.L. All Rights Reserved
#    Vicente Ángel Gutiérrez <vicente@comunitea.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PosOrder(models.Model):
    _inherit = "pos.order"

    paid_on_reservation = fields.Boolean("Paid on reservation", default=False)
    pms_reservation_id = fields.Many2one("pms.reservation", string="PMS reservation")

    def _get_fields_for_draft_order(self):
        res = super(PosOrder, self)._get_fields_for_draft_order()
        res.append("paid_on_reservation")
        res.append("pms_reservation_id")
        return res

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        order_fields["paid_on_reservation"] = ui_order.get("paid_on_reservation", False)
        order_fields["pms_reservation_id"] = ui_order.get("pms_reservation_id", False)
        return order_fields

    def _get_fields_for_order_line(self):
        res = super(PosOrder, self)._get_fields_for_order_line()
        res.append("pms_service_line_id")
        return res

    def _get_order_lines(self, orders):
        super(PosOrder, self)._get_order_lines(orders)
        for order in orders:
            if "lines" in order:
                for line in order["lines"]:
                    line[2]["pms_service_line_id"] = (
                        line[2]["pms_service_line_id"][0]
                        if line[2]["pms_service_line_id"]
                        else False
                    )

    @api.model
    def _process_order(self, pos_order, draft, existing_order):
        data = pos_order.get("data", False)
        if (
            data
            and data.get("paid_on_reservation", False)
            and data.get("pms_reservation_id", False)
        ):
            pms_reservation_id = data.pop("pms_reservation_id")
            res = super(PosOrder, self)._process_order(pos_order, draft, existing_order)
            order_id = self.env["pos.order"].browse(res)
            pms_reservation_id = (
                self.sudo().env["pms.reservation"].browse(pms_reservation_id)
            )
            if not pms_reservation_id:
                raise UserError(_("Reservation does not exists."))
            order_id.pms_reservation_id = pms_reservation_id.id
            order_id.add_order_lines_to_reservation(pms_reservation_id)
            return res
        else:
            return super()._process_order(pos_order, draft, existing_order)

    def add_order_lines_to_reservation(self, pms_reservation_id):
        self.lines.filtered(lambda x: not x.pms_service_line_id)._generate_pms_service(
            pms_reservation_id
        )


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    pms_service_line_id = fields.Many2one("pms.service.line", string="PMS Service line")

    def _generate_pms_service(self, pms_reservation_id):
        for line in self:
            vals = {
                "product_id": line.product_id.id,
                "reservation_id": pms_reservation_id.id,
                "is_board_service": False,
                "service_line_ids": [
                    (
                        0,
                        False,
                        {
                            "date": datetime.now(),
                            "price_unit": line.price_unit,
                            "discount": line.discount,
                            "day_qty": line.qty,
                        },
                    )
                ],
            }
            service = self.sudo().env["pms.service"].create(vals)

            line.write({"pms_service_line_id": service.service_line_ids.id})
