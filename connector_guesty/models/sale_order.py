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
    manually_confirmed = fields.Boolean(
        string="Manually Confirmed", track_visibility="onchange"
    )

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

    def action_draft(self):
        reservation_id = self.sale_get_active_reservation(include_cancelled=True)
        reservation_id.action_draft()
        return super().action_draft()

    def action_cancel(self, ignore_push_event=False, cancel_reservation=True):
        reservation_ids = self.sale_get_active_reservation()
        if reservation_ids and cancel_reservation:
            reservation_ids.with_context(
                ignore_push_event=ignore_push_event
            ).action_cancel()

        self.manually_confirmed = False
        return super().action_cancel()

    def action_approve(self, ignore_push_event=False):
        if not ignore_push_event:
            reservation_ids = self.sale_get_active_reservation()
            if reservation_ids:
                reservation_ids.guesty_push_reservation()
        return super().action_approve()

    def action_quotation_send(self):
        _log.info("================= Sending Email =================")
        rs = super().action_quotation_send()
        for record in self:
            to_create = record.sale_get_active_reservation().filtered(
                lambda r: not r.guesty_id
            )
            if to_create:
                default_status = "inquiry"
                if self.state in ["sale", "done"]:
                    default_status = "confirmed"
                to_create.guesty_push_reservation(default_status=default_status)
        return rs

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

    def sale_get_active_reservation(self, include_cancelled=False):
        _stage_ids = [
            self.env.company.guesty_backend_id.stage_reserved_id.id,
            self.env.company.guesty_backend_id.stage_confirmed_id.id,
            self.env.company.guesty_backend_id.stage_inquiry_id.id,
        ]

        if include_cancelled:
            _stage_ids.append(self.env.company.guesty_backend_id.stage_canceled_id.id)

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

    def manually_confirmed_emails(self):
        message_follower_ids = self.message_follower_ids.filtered(
            lambda x: x.partner_id.id != self.partner_id.id
        )
        partner_ids = message_follower_ids.mapped("partner_id").ids
        partner_ids_string = ",".join(map(str, partner_ids))
        return partner_ids_string

    def send_manually_confirmed_email(self):
        template_id = self.env.ref(
            "connector_guesty.mail_template_sale_manual_confirmation"
        )
        template_id.send_mail(self.id, force_send=True)

    def action_confirm(self):
        self.manually_confirmed = self._context.get("default_manually_confirmed")
        original_return = super(SaleOrder, self).action_confirm()

        reservations = self.sale_get_active_reservation()
        if reservations:
            if not self.has_to_be_paid():
                reservations.action_confirm()

        if self.manually_confirmed:
            try:
                self.send_manually_confirmed_email()
            except Exception as e:
                _log.error(e)
        return original_return
