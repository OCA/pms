# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, api, models
from odoo.exceptions import ValidationError

_log = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.constrains("currency_id")
    def _check_currency(self):
        for sale in self:
            reservation = self.env["pms.reservation"].search(
                [("sale_order_id", "=", sale.id)]
            )
            if reservation:
                guesty_price = reservation.property_id.reservation_ids.filtered(
                    lambda s: s.is_guesty_price
                )
                if guesty_price:
                    if guesty_price.currency_id.id != sale.currency_id.id:
                        raise ValidationError(
                            _(
                                "The selected listing does not support "
                                "the currency assigned in the SO"
                            )
                        )

    @api.model
    def create(self, values):
        res = super().create(values)
        return res

    def write(self, values):
        res = super().write(values)
        if (
            not self.env.context.get("ignore_guesty_push", False)
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
        return super(SaleOrder, self).action_cancel()
