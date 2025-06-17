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

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = "pos.session"

    def _load_model(self, model):
        return super(PosSession, self.with_context(pos_user_force=True))._load_model(
            model
        )

    def _accumulate_amounts(self, data):  # noqa: C901  # too-complex
        res = super()._accumulate_amounts(data)
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
                for element, value in dict(res["split_receivables_pay_later"]).items():
                    if (
                        element.payment_method_id
                        == self.config_id.pay_on_reservation_method_id
                    ):
                        value["amount"] = 0.0
                        value["amount_converted"] = 0.0

            else:
                for element, value in dict(
                    res["combine_receivables_pay_later"]
                ).items():
                    if element == self.config_id.pay_on_reservation_method_id:
                        value["amount"] = 0.0
                        value["amount_converted"] = 0.0
        return res

    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()
        if self.config_id.pay_on_reservation:
            result.append("pms.reservation")
        return result

    def _loader_params_pms_reservation(self):
        domain = [
            "|",
            ("state", "=", "onboard"),
            "&",
            ("checkout", "=", fields.Datetime.now().date()),
            ("state", "!=", "cancel"),
        ]
        if self.config_id and self.config_id.reservation_allowed_propertie_ids:
            domain.append(
                (
                    "pms_property_id",
                    "in",
                    self.config_id.reservation_allowed_propertie_ids.ids,
                )
            )
        return {
            "search_params": {
                "domain": domain,
                "fields": [
                    "name",
                    "id",
                    "state",
                    "service_ids",
                    "partner_name",
                    "adults",
                    "children",
                    "checkin",
                    "checkout",
                    "folio_internal_comment",
                    "rooms",
                ],
            },
        }

    def _loader_params_pms_service(self):
        return {
            "search_params": {
                "fields": [
                    "name",
                    "id",
                    "service_line_ids",
                    "product_id",
                    "reservation_id",
                ],
            },
        }

    def _loader_params_pms_service_line(self):
        return {
            "search_params": {
                "fields": [
                    "date",
                    "service_id",
                    "id",
                    "product_id",
                    "day_qty",
                    "pos_order_line_ids",
                ],
            },
        }

    def _loader_params_pos_order_line(self):
        return {
            "search_params": {
                "fields": [
                    "qty",
                    "id",
                    "pms_service_line_id",
                ],
            },
        }

    def _get_pos_ui_pms_reservation(self, params):
        ctx = {"pos_user_force": True}

        # 1. Obtener las reservas con `search_read` para todos los campos que necesitas
        reservations = (
            self.env["pms.reservation"]
            .with_context(**ctx)
            .search_read(**params["search_params"])
        )
        reservation_ids = [r["id"] for r in reservations]

        if not reservations:
            return []

        # 2. Obtener los servicios relacionados con esas reservas
        service_params = self._loader_params_pms_service()
        service_params["search_params"]["domain"] = [
            ("reservation_id", "in", reservation_ids)
        ]
        services = (
            self.env["pms.service"]
            .with_context(**ctx)
            .search_read(
                service_params["search_params"]["domain"],
                fields=service_params["search_params"]["fields"],
            )
        )
        service_ids = [s["id"] for s in services]

        # 3. Obtener las líneas de servicio relacionadas con esos servicios
        service_line_params = self._loader_params_pms_service_line()
        service_line_params["search_params"]["domain"] = [
            ("service_id", "in", service_ids)
        ]
        service_lines = (
            self.env["pms.service.line"]
            .with_context(**ctx)
            .search_read(
                service_line_params["search_params"]["domain"],
                fields=service_line_params["search_params"]["fields"],
            )
        )
        service_line_ids = [sl["id"] for sl in service_lines]

        # 4. Obtener las líneas de pedido POS relacionadas con esas líneas de servicio
        pos_order_line_params = self._loader_params_pos_order_line()
        pos_order_line_params["search_params"]["domain"] = [
            ("pms_service_line_id", "in", service_line_ids)
        ]
        pos_order_lines = (
            self.env["pos.order.line"]
            .with_context(**ctx)
            .search_read(
                pos_order_line_params["search_params"]["domain"],
                fields=pos_order_line_params["search_params"]["fields"],
            )
        )

        # 5. Agrupar las líneas de pedido por línea de servicio
        pos_order_lines_by_service_line = {}
        for pos_order_line in pos_order_lines:
            service_line_id = pos_order_line["pms_service_line_id"][0]
            if service_line_id not in pos_order_lines_by_service_line:
                pos_order_lines_by_service_line[service_line_id] = []
            pos_order_lines_by_service_line[service_line_id].append(pos_order_line)

        # 6. Agrupar las líneas de servicio por servicio
        service_lines_by_service = {}
        for service_line in service_lines:
            service_id = service_line["service_id"][0]
            if service_id not in service_lines_by_service:
                service_lines_by_service[service_id] = []
            service_line["pos_order_lines"] = pos_order_lines_by_service_line.get(
                service_line["id"], []
            )
            service_lines_by_service[service_id].append(service_line)

        # 7. Agrupar los servicios por reserva
        services_by_reservation = {}
        for service in services:
            reservation_id = service["reservation_id"][0]
            if reservation_id not in services_by_reservation:
                services_by_reservation[reservation_id] = []
            service["service_lines"] = service_lines_by_service.get(service["id"], [])
            services_by_reservation[reservation_id].append(service)

        # 8. Añadir los servicios dentro de las reservas
        for reservation in reservations:
            reservation["services"] = services_by_reservation.get(reservation["id"], [])

        return reservations

    def try_cash_in_out(self, _type, amount, reason, extras):
        sign = 1 if _type == "in" else -1
        sessions = self.filtered("cash_journal_id")
        if not sessions:
            raise UserError(_("There is no cash payment method for this PoS Session"))

        partner_id = self.env.context.get("partner_id", False)
        self.env["account.bank.statement.line"].sudo().create(
            [
                {
                    "pos_session_id": session.id,
                    "journal_id": session.cash_journal_id.id,
                    "amount": sign * amount,
                    "date": fields.Date.context_today(self),
                    "payment_ref": "-".join(
                        [session.name, extras["translatedType"], reason]
                    ),
                    "partner_id": partner_id,
                }
                for session in sessions
            ]
        )
        cashier = self.env.context.get("cashier", False)
        message_content = [f"-Cashier: {cashier}"] if cashier else []
        message_content.append(f'-Cash {extras["translatedType"]}')
        message_content.append(f'-Amount: {extras["formattedAmount"]}')
        if reason:
            message_content.append(f"-Reason: {reason}")
        self.message_post(body="<br/>\n".join(message_content))

    def set_cashbox_pos(self, cashbox_value, notes):
        res = super().set_cashbox_pos(cashbox_value, notes)
        cashier = self.env.context.get("cashier", False)
        if cashier:
            self.message_post(
                body=_(
                    "Session opened by cashier: "
                    '<strong style="text-transform:uppercase;">{cashier}<strong/>'
                ).format(cashier=cashier)
            )
        return res

    def close_session_from_ui(self, bank_payment_method_diff_pairs=None):
        result = super().close_session_from_ui(bank_payment_method_diff_pairs)
        if result.get("successful"):
            cashier = self.env.context.get("cashier", False)
            if cashier:
                self.message_post(
                    body=_(
                        "Session ended by cashier: "
                        '<strong style="text-transform:uppercase;">{cashier}<strong/>'
                    ).format(cashier=cashier)
                )
        return result
