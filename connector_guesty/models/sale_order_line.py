# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import fields, models

_log = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    guesty_is_locked = fields.Boolean(default=False)
    guesty_type = fields.Char()
    guesty_normal_type = fields.Char()
    guesty_second_identifier = fields.Char()
    allow_discount = fields.Boolean(related="product_id.allow_discount")

    def write(self, values):
        return super().write(values)

    def _get_display_price(self, product):
        return super()._get_display_price(
            product.with_context(
                {
                    "property_id": self.sudo().property_id,
                    "reservation_start": self.start,
                    "reservation_stop": self.stop,
                    "reservation_date": self.order_id.date_order,
                }
            )
        )
