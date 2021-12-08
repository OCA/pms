# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import logging

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_log = logging.getLogger(__name__)


class PmsReservation(models.Model):
    _inherit = "pms.reservation"

    guesty_id = fields.Char()

    @api.constrains("property_id", "stage_id", "start", "stop")
    def _check_no_of_reservations(self):
        if self.env.context.get("ignore_overlap"):
            return

        # noinspection PyProtectedMember
        return super(PmsReservation, self)._check_no_of_reservations()

    @api.model
    def create(self, values):
        res = super(PmsReservation, self).create(values)
        if not res.property_id.guesty_id:
            raise ValidationError(_("Property not linked to guesty"))

        # Set the automated workflow to create and validate the invoice
        if res.sale_order_id and not res.sale_order_id.workflow_process_id:
            res.sale_order_id.with_context({"ignore_guesty_push": True}).write(
                {
                    "workflow_process_id": self.env.ref(
                        "sale_automatic_workflow.automatic_validation"
                    ).id
                }
            )

        if not self.env.context.get("ignore_guesty_push", False):
            res.with_delay().guesty_push_reservation()

        return res

    def write(self, values):
        res = super(PmsReservation, self).write(values)
        if self.guesty_id and not self.env.context.get("ignore_guesty_push", False):
            self.with_delay().guesty_push_reservation_update()
        return res

    def action_book(self):
        res = super(PmsReservation, self).action_book()
        _log.info("Booking on guesty.....")
        if not self.env.context.get("ignore_guesty_push", False):
            _log.info("Allowed: Booking on guesty.....")
            if not res:
                raise UserError(_("Something went wrong"))

            self.guesty_check_availability()

            # Send to guesty
            self.guesty_push_reservation_reserve()
        return res

    def action_confirm(self):
        res = super(PmsReservation, self).action_confirm()
        if not self.env.context.get("ignore_guesty_push", False):
            if not res:
                raise UserError(_("Something went wrong"))

            status = self.guesty_get_status()
            if status not in ["inquiry", "reserved"]:
                raise ValidationError(_("Unable to confirm reservation"))
            # Send to guesty
            self.guesty_push_reservation_confirm()
        return res

    def action_cancel(self):
        res = super(PmsReservation, self).action_cancel()
        if self.guesty_id and not self.env.context.get("ignore_guesty_push", False):
            self.guesty_push_reservation_cancel()
        return res

    def guesty_check_availability(self):
        real_stop_date = self.stop - datetime.timedelta(days=1)
        calendar_dates = self.property_id.guesty_get_calendars(
            self.start, real_stop_date
        )

        if any([calendar["status"] != "available" for calendar in calendar_dates]):
            raise ValidationError(_("Dates for this reservation are not available"))

    def guesty_get_status(self):
        backend = self.env.company.guesty_backend_id
        success, result = backend.call_get_request(
            url_path="reservations/{}".format(self.guesty_id),
            params={"fields": ", ".join(["status"])},
        )

        if success:
            return result.get("status")
        else:
            raise ValidationError(_("Unable to verify reservation"))

    def guesty_push_reservation_cancel(self):
        body = {
            "status": "canceled",
            "canceledBy": self.env.user.name,
        }
        backend = self.env.company.guesty_backend_id
        success, result = backend.call_put_request(
            url_path="reservations/{}".format(self.guesty_id), body=body
        )

        if not success:
            self.message_post(body=_("Reservations cannot be canceled"))
            raise UserError(_("Unable to cancel reservation"))

        self.message_post(body=_("Reservation cancelled successfully on guesty!"))

    def guesty_push_reservation_reserve(self):
        backend = self.env.company.guesty_backend_id
        body = self.parse_push_reservation_data(backend)
        body["status"] = "reserved"

        success, result = backend.call_put_request(
            url_path="reservations/{}".format(self.guesty_id), body=body
        )

        if not success:
            raise UserError(_("Unable to reserve reservation"))

        self.message_post(body=_("Reservation reserved successfully on guesty!"))

    def guesty_push_reservation_confirm(self):
        backend = self.env.company.guesty_backend_id
        body = self.parse_push_reservation_data(backend)
        body["status"] = "confirmed"

        success, result = backend.call_put_request(
            url_path="reservations/{}".format(self.guesty_id), body=body
        )

        if not success:
            raise UserError(_("Unable to confirm reservation"))

        self.message_post(body=_("Reservation confirmed successfully on guesty!"))

    def guesty_push_reservation_update(self):
        backend = self.env.company.guesty_backend_id
        if not backend:
            raise ValidationError(_("No backend defined"))

        body = self.parse_push_reservation_data(backend)
        success, res = backend.call_put_request(
            url_path="reservations/{}".format(self.guesty_id), body=body
        )
        if not success:
            raise UserError(_("Unable to send to guesty"))

    # def guesty_push_reservation_extra_lines(self):
    #     if self.guesty_id and self.sale_order_id and self.env.company.guesty_backend_id:
    #         for line in self.sale_order_id.order_line:

    def guesty_push_reservation(self):
        backend = self.env.company.guesty_backend_id
        if not backend:
            raise ValidationError(_("No backend defined"))

        if self.sale_order_id:
            # create a reservation on guesty
            body = self.parse_push_reservation_data(backend)
            body["status"] = "inquiry"

            success, res = backend.call_post_request(url_path="reservations", body=body)
            if not success:
                raise UserError(_("Unable to send to guesty"))

            guesty_id = res.get("_id")
            self.guesty_id = guesty_id
        else:
            # retrieve calendars
            success, calendars = backend.call_get_request(
                url_path="listings/{}/calendar".format(self.property_id.guesty_id),
                params={
                    "from": self.start.strftime("%Y-%m-%d"),
                    "to": self.stop.strftime("%Y-%m-%d"),
                },
            )

            if success:
                for calendar in calendars:
                    if calendar.get("status") != "available":
                        raise ValidationError(
                            _("Date {}, are not available to be blocked").format(
                                calendar.get("date")
                            )
                        )

                # todo: build a context title with the next format
                # block title examples
                # OPS-MNT-WKB AC Repair - Bedroom
                # DEV - PRE - EVC  No live
                # OPS - ROM - UNV exit unit
                block_title = "Blocked By: {}".format(self.partner_id.name)
                backend.call_put_request(
                    url_path="listings/calendars",
                    body={
                        "listings": [self.property_id.guesty_id],
                        "from": self.start.strftime("%Y-%m-%d"),
                        "to": self.stop.strftime("%Y-%m-%d"),
                        "status": "unavailable",
                        "note": block_title,
                    },
                )

    def guesty_pull_reservation(self, backend, payload):
        _id, reservation = self.sudo().guesty_parse_reservation(payload, backend)
        reservation_id = self.sudo().search([("guesty_id", "=", _id)], limit=1)

        if not reservation_id:
            reservation_id = (
                self.env["pms.reservation"]
                .sudo()
                .with_context({"ignore_overlap": True, "ignore_guesty_push": True})
                .create(reservation)
            )

            invoice_lines = payload.get("money", {}).get("invoiceItems")
            no_nights = payload.get("nightsCount", 0)
            status = payload.get("status", "inquiry")

            reservation_id.build_so(invoice_lines, no_nights, status, backend)
        else:
            _log.info("Update reservation: {}".format(reservation_id.guesty_id))
            reservation_id.sudo().with_context(
                {"ignore_overlap": True, "ignore_guesty_push": True}
            ).write(reservation)

        return True

    def guesty_parse_reservation(self, reservation, backend):
        guesty_id = reservation.get("_id")
        listing_id = reservation.get("listingId")
        check_in = reservation.get("checkIn")
        check_out = reservation.get("checkOut")
        guest_id = reservation.get("guestId")

        property_id = self.env["pms.property"].search(
            [("guesty_id", "=", listing_id)], limit=1
        )

        if not property_id.exists():
            raise ValidationError(_("Listing: {} does not exist".format(listing_id)))

        pms_guest = backend.sudo().guesty_search_pull_customer(guest_id)

        check_in_time = datetime.datetime.strptime(check_in[0:19], "%Y-%m-%dT%H:%M:%S")
        check_out_time = datetime.datetime.strptime(
            check_out[0:19], "%Y-%m-%dT%H:%M:%S"
        )

        return guesty_id, {
            "guesty_id": guesty_id,
            "property_id": property_id.id,
            "start": check_in_time,
            "stop": check_out_time,
            "partner_id": pms_guest.partner_id.id,
        }

    def parse_push_reservation_data(self, backend):
        customer = backend.guesty_search_create_customer(self.partner_id)

        utc = pytz.UTC
        tz = pytz.timezone(self.property_id.tz or "America/Mexico_City")
        checkin_localized = utc.localize(self.start).astimezone(tz)
        checkout_localized = utc.localize(self.stop).astimezone(tz)

        body = {
            "listingId": self.property_id.guesty_id,
            "checkInDateLocalized": checkin_localized.strftime("%Y-%m-%d"),
            "checkOutDateLocalized": checkout_localized.strftime("%Y-%m-%d"),
            "guestId": customer.guesty_id,
            "money": {},
        }

        reservation_line = self.sale_order_id.order_line.filtered(
            lambda s: s.reservation_ok
        )
        if reservation_line:
            body["money"] = {
                "fareAccommodation": reservation_line.price_subtotal,
                "currency": self.sale_order_id.currency_id.name,
            }

        cleaning_line = self.sale_order_id.order_line.filtered(
            lambda s: s.product_id.id == backend.cleaning_product_id.id
        )

        if cleaning_line and reservation_line:
            body["money"]["fareCleaning"] = cleaning_line.price_subtotal

        extra_lines = self.sale_order_id.order_line.filtered(
            lambda s: not s.reservation_ok
            and s.id != cleaning_line.id
            and not s.guesty_is_locked
        )

        if extra_lines:
            body["money"]["invoiceItems"] = []
            for line in extra_lines:
                line_amount = line.price_subtotal
                line_payload = {
                    "type": "MANUAL",
                    "title": line.name,
                    "amount": line_amount,
                    "currency": self.sale_order_id.currency_id.name,
                }

                if line.guesty_type:
                    line_payload["type"] = line.guesty_type
                if line.guesty_normal_type:
                    line_payload["normalType"] = line.guesty_normal_type
                if line.guesty_second_identifier:
                    line_payload["secondIdentifier"] = line.guesty_second_identifier

                body["money"]["invoiceItems"].append(line_payload)
        else:
            body["money"]["invoiceItems"] = []

        return body

    def build_so(self, guesty_invoice_items, no_nights, status, backend):
        # Create SO based on reservation
        # When the reservation was created out of odoo
        if guesty_invoice_items is None:
            _log.error("Unable to create SO without guesty data")
            return

        if not backend:
            raise ValidationError(_("No Backend defined"))

        # if self.sale_order_id:
        #     return self.sale_order_id

        if status in ["inquiry", "reserved", "confirmed"]:
            order_lines = []
            for line in guesty_invoice_items:
                if line.get("type") in ["TAX", "CITY_TAX"]:
                    continue  # ignore the tax items
                elif line.get("type") == "ACCOMMODATION_FARE":
                    reservation_type = self.property_id.reservation_ids.filtered(
                        lambda s: s.is_guesty_price
                    )

                    if not reservation_type:
                        raise ValidationError(_("Missing guesty reservation type"))

                    line_amount = line.get("amount")
                    line_amount = float(line_amount)
                    line_price_unit = line_amount / no_nights
                    order_lines.append(
                        {
                            "product_id": reservation_type.product_id.id,
                            "name": reservation_type.display_name,
                            "product_uom_qty": no_nights,
                            "price_unit": line_price_unit,
                            "property_id": self.property_id.id,
                            "reservation_id": reservation_type.id,
                            "pms_reservation_id": self.id,
                            "start": self.start,
                            "stop": self.stop,
                            "no_of_guests": 1,  # Todo: Set correct number of guests
                        }
                    )
                elif line.get("type") == "CLEANING_FEE":
                    order_lines.append(
                        {
                            "product_id": backend.sudo().cleaning_product_id.id,
                            "name": backend.sudo().cleaning_product_id.name,
                            "product_uom_qty": 1,
                            "price_unit": line.get("amount"),
                        }
                    )
                else:
                    line_amount = line.get("amount")
                    line_amount = float(line_amount)

                    order_lines.append(
                        {
                            "guesty_is_locked": line.get("isLocked") or False,
                            "guesty_type": line.get("type"),
                            "guesty_normal_type": line.get("normalType"),
                            "guesty_second_identifier": line.get("secondIdentifier"),
                            "product_id": backend.sudo().extra_product_id.id,
                            "name": line.get("title"),
                            "product_uom_qty": 1,
                            "price_unit": line_amount,
                        }
                    )

            if not self.sale_order_id:
                accommodation_line = [
                    line
                    for line in guesty_invoice_items
                    if line.get("type") == "ACCOMMODATION_FARE"
                ]
                guesty_currency = accommodation_line[0].get("currency")
                if not guesty_currency:
                    guesty_currency = "USD"

                currency_id = (
                    self.env["res.currency"]
                    .sudo()
                    .search([("name", "=", guesty_currency)])
                )

                if not currency_id:
                    raise ValidationError(
                        _("Currency: {} Not found").format(guesty_currency)
                    )

                price_list = (
                    self.env["product.pricelist"]
                    .sudo()
                    .search([("currency_id", "=", currency_id.id)])
                )

                if not price_list:
                    raise ValidationError(
                        _("No pricelist found for {}").format(guesty_currency)
                    )

                so = (
                    self.env["sale.order"]
                    .sudo()
                    .create(
                        {
                            "partner_id": self.partner_id.id,
                            "pricelist_id": price_list.id,
                            "order_line": [(0, False, line) for line in order_lines],
                        }
                    )
                )

                self.sudo().with_context({"ignore_guesty_push": True}).write(
                    {"sale_order_id": so.id}
                )
            elif self.sale_order_id.state == "draft":
                updated_lines = [(6, False, False)] + [
                    (0, False, line) for line in order_lines
                ]
                self.sale_order_id.with_context({"ignore_guesty_push": True}).write(
                    {"order_line": updated_lines}
                )

            if (
                status in ["reserved", "confirmed"]
                and self.sale_order_id.state == "draft"
            ):
                self.sale_order_id.with_context(
                    {"ignore_guesty_push": True}
                ).action_confirm()  # confirm the SO -> Reservation booked

            if status == "confirmed":
                self.with_context(
                    {"ignore_guesty_push": True}
                ).action_confirm()  # confirm the reservation

        elif status in ["canceled", "declined", "expired", "closed"]:
            stage_id = self.env.ref(
                "pms_sale.pms_stage_cancelled", raise_if_not_found=False
            )

            self.write({"stage_id": stage_id.id})
