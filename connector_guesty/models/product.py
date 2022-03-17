# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import logging

from odoo import models

_log = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    def price_compute(self, price_type):
        result = super().price_compute(price_type)
        for product in self:
            if product.reservation_ok and self.env.company.guesty_backend_id:
                property_id = self.env.context.get("property_id")
                reservation_start = self.env.context.get("reservation_start")
                reservation_stop = self.env.context.get("reservation_stop")
                reservation_date = self.env.context.get("reservation_date")
                if (
                    property_id
                    and reservation_start
                    and reservation_stop
                    and reservation_date
                ):
                    price = product.compute_reservation_price(
                        property_id,
                        reservation_start,
                        reservation_stop,
                        reservation_date,
                    )
                    if price:
                        result[product.id] = price
        return result

    def compute_reservation_price(self, property_id, start, stop, reservation_date):
        real_stop_date = stop - datetime.timedelta(days=1)
        success, result = self.env.company.guesty_backend_id.call_get_request(
            url_path="availability-pricing/api/calendar/listings/{}".format(
                property_id.guesty_id
            ),
            params={
                "startDate": start.strftime("%Y-%m-%d"),
                "endDate": real_stop_date.strftime("%Y-%m-%d"),
            },
            paginate=False,
        )
        if not success:
            return None

        dates_list = result["data"]["days"]
        if len(dates_list) == 0:
            return None

        prices = [calendar.get("price", 0.0) for calendar in dates_list]
        avg_price = sum(prices) / len(prices)

        currency_name = dates_list[0]["currency"]
        currency_id = (
            self.env["res.currency"]
            .sudo()
            .search([("name", "=", currency_name)], limit=1)
        )

        if not currency_id:
            currency_id = self.sudo().env.ref("base.USD", raise_if_not_found=False)

        # noinspection PyProtectedMember
        price_currency = currency_id._convert(
            avg_price,
            self.currency_id,
            self.env.company,
            reservation_date,
        )

        return price_currency
