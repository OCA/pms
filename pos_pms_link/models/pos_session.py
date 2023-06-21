##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2023 Comunitea Servicios Tecnológicos S.L. All Rights Reserved
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

import logging
from collections import defaultdict

from odoo import models

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = "pos.session"

    def _accumulate_amounts(self, data):  # noqa: C901  # too-complex
        res = super(PosSession, self)._accumulate_amounts(data)
        if (
            self.config_id.pay_on_reservation
            and self.config_id.pay_on_reservation_method_id
        ):
            amounts = lambda: {"amount": 0.0, "amount_converted": 0.0}  # noqa E731
            tax_amounts = lambda: {  # noqa: E731
                "amount": 0.0,
                "amount_converted": 0.0,
                "base_amount": 0.0,
                "base_amount_converted": 0.0,
            }
            sales = defaultdict(amounts)
            taxes = defaultdict(tax_amounts)
            rounded_globally = (
                self.company_id.tax_calculation_rounding_method == "round_globally"
            )

            reservation_orders = self.order_ids.filtered(lambda x: x.pms_reservation_id)

            order_taxes = defaultdict(tax_amounts)
            for order_line in reservation_orders.lines:
                line = self._prepare_line(order_line)
                # Combine sales/refund lines
                sale_key = (
                    # account
                    line["income_account_id"],
                    # sign
                    -1 if line["amount"] < 0 else 1,
                    # for taxes
                    tuple(
                        (tax["id"], tax["account_id"], tax["tax_repartition_line_id"])
                        for tax in line["taxes"]
                    ),
                    line["base_tags"],
                )
                sales[sale_key] = self._update_amounts(
                    sales[sale_key], {"amount": line["amount"]}, line["date_order"]
                )
                # Combine tax lines
                for tax in line["taxes"]:
                    tax_key = (
                        tax["account_id"] or line["income_account_id"],
                        tax["tax_repartition_line_id"],
                        tax["id"],
                        tuple(tax["tag_ids"]),
                    )
                    order_taxes[tax_key] = self._update_amounts(
                        order_taxes[tax_key],
                        {"amount": tax["amount"], "base_amount": tax["base"]},
                        tax["date_order"],
                        round=not rounded_globally,
                    )
            for tax_key, amounts in order_taxes.items():
                if rounded_globally:
                    amounts = self._round_amounts(amounts)
                for amount_key, amount in amounts.items():
                    taxes[tax_key][amount_key] += amount

            for element, value in dict(res["taxes"]).items():
                if element in taxes:
                    value["amount"] = value["amount"] - taxes[element]["amount"]
                    value["amount_converted"] = (
                        value["amount_converted"] - taxes[element]["amount_converted"]
                    )
                    value["base_amount"] = (
                        value["base_amount"] - taxes[element]["base_amount"]
                    )
                    value["base_amount_converted"] = (
                        value["base_amount_converted"]
                        - taxes[element]["base_amount_converted"]
                    )

            for element, value in dict(res["sales"]).items():
                if element in sales:
                    value["amount"] = value["amount"] - sales[element]["amount"]
                    value["amount_converted"] = (
                        value["amount_converted"] - sales[element]["amount_converted"]
                    )

            if self.config_id.pay_on_reservation_method_id.split_transactions:
                for element, value in dict(res["split_receivables"]).items():
                    if (
                        element.payment_method_id
                        == self.config_id.pay_on_reservation_method_id
                    ):
                        value["amount"] = 0.0
                        value["amount_converted"] = 0.0

            else:
                for element, value in dict(res["combine_receivables"]).items():
                    if element == self.config_id.pay_on_reservation_method_id:
                        value["amount"] = 0.0
                        value["amount_converted"] = 0.0
        return res
