# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, http
from odoo.exceptions import UserError
from odoo.http import request

from odoo.addons.sale.controllers.portal import CustomerPortal

_log = logging.getLogger(__name__)


class SaleCustomerPortal(CustomerPortal):
    @http.route(
        ["/my/orders/<int:order_id>/transaction/"],
        type="json",
        auth="public",
        website=True,
    )
    def payment_transaction_token(
        self, acquirer_id, order_id, save_token=False, access_token=None, **kwargs
    ):
        if order_id:
            s_order = request.env["sale.order"].sudo().browse(int(order_id))
            if s_order and s_order.reservation_count > 0:
                state_ids = [
                    request.env.ref(
                        "pms_sale.pms_stage_booked", raise_if_not_found=False
                    ).id,
                    request.env.ref(
                        "pms_sale.pms_stage_new", raise_if_not_found=False
                    ).id,
                ]

                reservation = (
                    request.env["pms.reservation"]
                    .sudo()
                    .search(
                        [
                            ("sale_order_id", "=", int(order_id)),
                            ("stage_id", "in", state_ids),
                        ],
                        limit=1,
                    )
                )

                if reservation:
                    reservation.guesty_check_availability()
                else:
                    raise UserError(_("Error validating the order"))

        return super(SaleCustomerPortal, self).payment_transaction_token(
            acquirer_id, order_id, save_token, access_token, **kwargs
        )
