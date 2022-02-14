# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from datetime import datetime, timedelta

from odoo import api, models

_log = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def create(self, values):
        return super().create(values)

    def write(self, values):
        res = super().write(values)
        if (
            self.company_id.guesty_backend_id
            and not self.env.context.get("ignore_guesty_push", False)
            and "order_line" in values
        ):
            for sale in self:
                reservation = self.env["pms.reservation"].search(
                    [("sale_order_id", "=", sale.id)]
                )
                if reservation and reservation.guesty_id:
                    reservation.with_delay().guesty_push_reservation_update()
        return res

    def action_cancel(self):
        stage_ids = [
            self.env.ref("pms_sale.pms_stage_new", raise_if_not_found=False).id,
            self.env.ref("pms_sale.pms_stage_booked", raise_if_not_found=False).id,
            self.env.ref("pms_sale.pms_stage_confirmed", raise_if_not_found=False).id,
        ]
        reservation_ids = self.env["pms.reservation"].search(
            [("sale_order_id", "=", self.id), ("stage_id", "in", stage_ids)]
        )
        reservation_ids.action_cancel()
        return super().action_cancel()

    @api.onchange("order_line")
    def _onchange_validity_date(self):
        for order_line in self.order_line:
            if order_line.property_id:
                days_quotation_expiration = (
                    order_line.property_id.days_quotation_expiration
                )
                self.validity_date = datetime.now() + timedelta(
                    days=days_quotation_expiration
                )
                break

    def sale_get_active_reservation(self):
        _stage_ids = [
            self.env.company.guesty_backend_id.stage_reserved_id.id,
            self.env.company.guesty_backend_id.stage_confirmed_id.id,
            self.env.company.guesty_backend_id.stage_inquiry_id.id,
        ]

        _reservation = (
            self.env["pms.reservation"]
            .sudo()
            .search(
                [("sale_order_id", "=", self.id), ("stage_id", "in", _stage_ids)],
                limit=1,
            )
        )

        return _reservation
