# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_log = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    pms_reservation_id = fields.Many2one(
        "pms.reservation", compute="_compute_pms_reservation_id", store=True
    )
    pms_property_id = fields.Many2one(
        "pms.property", compute="_compute_pms_reservation_id", store=True
    )

    check_in = fields.Datetime(related="pms_reservation_id.start")
    check_out = fields.Datetime(related="pms_reservation_id.stop")

    @api.depends("order_line")
    def _compute_pms_reservation_id(self):
        for sale in self:
            reservation = sale.sale_get_active_reservation()
            if reservation:
                sale.pms_reservation_id = reservation.id
                sale.pms_property_id = reservation.property_id.id

    @api.model
    def create(self, values):
        return super().create(values)

    def write(self, values):
        res = super().write(values)
        _fields = [f for f in values if f in ["order_line", "state"]]

        if (
            self.company_id.guesty_backend_id
            and not self.env.context.get("ignore_guesty_push", False)
            and len(_fields) > 0
        ):
            for sale in self:
                if sale.state == "draft":
                    continue

                reservation_ids = self.env["pms.reservation"].search(
                    [("sale_order_id", "=", sale.id)]
                )

                if reservation_ids:
                    for reservation in reservation_ids:
                        if reservation.guesty_id:
                            reservation.guesty_push_reservation_update()
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

    def action_reserve(self):
        reservation = self.sale_get_active_reservation()
        if (
            reservation.stage_id.id
            == self.env.company.guesty_backend_id.stage_inquiry_id.id
        ):
            reservation.action_book()
            self.message_post(body=_("Reservation successfully reserved"))
        elif (
            reservation.stage_id.id
            == self.env.company.guesty_backend_id.stage_reserved_id.id
        ):
            raise UserError(_("Reservation is already reserved"))
        else:
            raise UserError(_("Unable to reserve"))

    def action_send_multi_quote(self):
        for sale in self:
            try:
                template_id = sale._find_mail_template()
                if template_id:
                    sale.with_context(force_send=True).message_post_with_template(
                        template_id,
                        composition_mode="comment",
                        email_layout_xmlid="mail.mail_notification_paynow",
                    )
                    sale.action_quotation_sent()
            except Exception as ex:
                _log.error(ex)
