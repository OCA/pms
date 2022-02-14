# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import logging

from odoo import _, api, models
from odoo.exceptions import ValidationError

_log = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    @api.model
    def create(self, values):
        res = super().create(values)
        cancel_stage_id = self.env.ref(
            "pms_sale.pms_stage_cancelled", raise_if_not_found=False
        )

        for sale in res.sale_order_ids:
            if sale.state == "cancel":
                raise ValidationError(_("Order was canceled"))

            reservation_id = (
                self.env["pms.reservation"]
                .sudo()
                .search(
                    [
                        ("sale_order_id", "=", sale.id),
                        ("stage_id", "not in", [cancel_stage_id.id]),
                    ],
                    limit=1,
                )
            )

            if reservation_id:
                bypass_stage = reservation_id.stage_id in [
                    self.env.company.guesty_backend_id.stage_reserved_id,
                    self.env.company.guesty_backend_id.stage_confirmed_id,
                ]

                if (
                    sale.validity_date
                    and sale.validity_date < datetime.datetime.now().date()
                ) and not bypass_stage:
                    raise ValidationError(_("Order was expired"))

                try:
                    reservation_id.guesty_check_availability()
                except Exception as ex:
                    _log.error(ex)
                    raise ValidationError(_("Reservation dates are not available"))
        return res

    def _set_transaction_done(self):
        res = super()._set_transaction_done()
        if self.state == "done" and self.env.company.guesty_backend_id:
            cancel_stage_id = self.env.ref(
                "pms_sale.pms_stage_cancelled", raise_if_not_found=False
            )
            for sale in self.sale_order_ids:
                reservation_id = (
                    self.env["pms.reservation"]
                    .sudo()
                    .search(
                        [
                            ("sale_order_id", "=", sale.id),
                            ("stage_id", "not in", [cancel_stage_id.id]),
                        ],
                        limit=1,
                    )
                )
                if reservation_id:
                    reservation_id.guesty_push_payment()

        return res
