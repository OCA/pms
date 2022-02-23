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

    def _cancel_expired_cron(self):
        if not self.env.company.guesty_backend_id.cancel_expired_quotes:
            _log.info("Expired orders cancellation is disabled")
            return

        _sales = self.env["sale.order"].search(
            [
                ("validity_date", "!=", False),
                ("validity_date", "<", datetime.datetime.now().date()),
                ("state", "=", "draft"),
            ]
        )

        _log.info("Expired sale orders : {}".format(_sales))

        for _sale in _sales:
            _reservation = _sale.sale_get_active_reservation()
            if (
                _reservation
                and _reservation.stage_id != self.env.company.stage_inquiry_id.id
            ):
                _sale.action_cancel()
                _sale.message_post(body=_("Canceled by expired date"))

    @api.constrains("property_id", "stage_id", "start", "stop")
    def _check_no_of_reservations(self):
        if self.env.context.get("ignore_overlap"):
            return

        # noinspection PyProtectedMember
        return super(PmsReservation, self)._check_no_of_reservations()

    @api.model
    def create(self, values):
        res = super(PmsReservation, self).create(values)
        if self.env.company.guesty_backend_id and not res.property_id.guesty_id:
            raise ValidationError(_("The property is not linked to Guesty."))

        # Set the automated workflow to create and validate the invoice
        if (
            self.env.company.guesty_backend_id
            and res.sale_order_id
            and not res.sale_order_id.workflow_process_id
        ):
            res.sale_order_id.with_context({"ignore_guesty_push": True}).write(
                {
                    "workflow_process_id": self.env.ref(
                        "sale_automatic_workflow.automatic_validation"
                    ).id
                }
            )
        if self.env.company.guesty_backend_id and not self.env.context.get(
            "ignore_guesty_push", False
        ):
            res.guesty_push_reservation()
        return res

    def write(self, values):
        res = super(PmsReservation, self).write(values)
        if (
            self.env.company.guesty_backend_id
            and self.guesty_id
            and not self.env.context.get("ignore_guesty_push", False)
        ):
            self.with_delay().guesty_push_reservation_update()
        return res

    def action_book(self):
        if (
            self.env.company.guesty_backend_id
            and self.stage_id.id
            != self.env.company.guesty_backend_id.stage_inquiry_id.id
        ):
            return False

        res = super(PmsReservation, self).action_book()
        if self.env.company.guesty_backend_id and not self.env.context.get(
            "ignore_guesty_push", False
        ):
            if not res:
                raise UserError(_("Something went wrong"))
            self.guesty_check_availability()
            # Send to Guesty
            self.guesty_push_reservation_reserve()
        return res

    def action_confirm(self):
        # If the reservation is already confirmed, we don´t do more
        if self.stage_id.id == self.env.company.guesty_backend_id.stage_confirmed_id.id:
            return None

        res = super(PmsReservation, self).action_confirm()

        if self.env.company.guesty_backend_id and not self.env.context.get(
            "ignore_guesty_push", False
        ):
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
        if (
            self.env.company.guesty_backend_id
            and self.guesty_id
            and not self.env.context.get("ignore_guesty_push", False)
        ):
            self.guesty_push_reservation_cancel()
        return res

    def guesty_check_availability(self):
        if self.stage_id.id == self.env.ref("pms_sale.pms_stage_booked").id:
            return True
        if self.stage_id.id == self.env.ref("pms_sale.pms_stage_confirmed").id:
            return True

        real_stop_date = self.stop - datetime.timedelta(days=1)
        calendar_dates = self.property_id.guesty_get_calendars(
            self.start, real_stop_date
        )

        if any([calendar["status"] != "available" for calendar in calendar_dates]):
            raise ValidationError(_("Dates for this reservation are not available"))

        _log.info("Dates are available")
        return True

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
            _log.error(result)
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
            raise UserError(_("Unable to confirm reservation : {}".format(result)))

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
            raise UserError(_("Unable to send to guesty") + str(res))

    def guesty_push_payment(self):
        backend = self.env.company.guesty_backend_id
        # give 5 minutes of overdue
        paid_time = datetime.datetime.now() + datetime.timedelta(minutes=5)
        payload = {
            "amount": self.sale_order_id.amount_total,
            "paymentMethod": {"method": "CASH"},
            "shouldBePaidAt": paid_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "paidAt": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "note": "Odoo Payment",
            "status": "SUCCEEDED",
        }
        success, result = backend.call_post_request(
            url_path="reservations/{}/payments".format(self.guesty_id), body=payload
        )

        if success:
            return result
        else:
            _log.error(result)

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
                if "Invalid dates" in res:
                    raise ValidationError(
                        _("Invalid dates {} - {}".format(self.start, self.stop))
                    )
                raise UserError(_("Unable to send to guesty") + ": " + str(res))

            guesty_id = res.get("_id")
            self.with_context(ignore_guesty_push=True).write({"guesty_id": guesty_id})
        else:
            # retrieve calendars
            # todo: Fix Calendar
            success, calendars = backend.call_get_request(
                url_path="availability-pricing/api/calendar/listings/{}".format(
                    self.property_id.guesty_id
                ),
                paginate=False,
                params={
                    "startDate": self.start.strftime("%Y-%m-%d"),
                    "endDate": self.stop.strftime("%Y-%m-%d"),
                },
            )

            if success:
                calendar_data = calendars.get("data", {}).get("days", [])
                for calendar in calendar_data:
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
                # todo: Fix Calendar Push
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

        context = {"ignore_overlap": True, "ignore_guesty_push": True}

        if not reservation_id:
            reservation_id = (
                self.env["pms.reservation"]
                .sudo()
                .with_context(context)
                .create(reservation)
            )
        else:
            _log.info("Update reservation: {}".format(reservation_id.guesty_id))
            reservation_id.sudo().with_context(context).write(reservation)

        invoice_lines = payload.get("money", {}).get("invoiceItems")
        no_nights = payload.get("nightsCount", 0)
        status = payload.get("status", "inquiry")

        reservation_id.with_context(context).with_delay().build_so(
            invoice_lines, no_nights, status, backend
        )

        return reservation_id

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
        guesty_listing_price = self.property_id.reservation_ids.filtered(
            lambda s: s.is_guesty_price
        )

        customer = backend.guesty_search_create_customer(self.partner_id)

        utc = pytz.UTC
        tz = pytz.timezone(self.property_id.tz or backend.timezone)
        checkin_localized = utc.localize(self.start).astimezone(tz)
        checkout_localized = utc.localize(self.stop).astimezone(tz)

        guesty_currency = guesty_listing_price.currency_id or backend.currency_id

        body = {
            "listingId": self.property_id.guesty_id,
            "checkInDateLocalized": checkin_localized.strftime("%Y-%m-%d"),
            "checkOutDateLocalized": checkout_localized.strftime("%Y-%m-%d"),
            "guestId": customer.guesty_id,
            "money": {"invoiceItems": []},
        }

        reservation_line = self.sale_order_id.order_line.filtered(
            lambda s: s.reservation_ok
        )
        if reservation_line:
            fare_acc_amount = (
                reservation_line.price_unit * reservation_line.product_uom_qty
            )
            fare_accomodation = self.sale_order_id.currency_id._convert(
                fare_acc_amount,
                guesty_currency,
                self.sale_order_id.company_id,
                self.sale_order_id.date_order,
            )
            body["money"] = {
                "fareAccommodation": fare_accomodation,
                "currency": guesty_currency.name,
            }

            if reservation_line.discount != 0:
                discount_amount = fare_accomodation / 100.0 * reservation_line.discount
                if "invoiceItems" not in body["money"]:
                    body["money"]["invoiceItems"] = []

                body["money"]["invoiceItems"].append(
                    {
                        "type": "MANUAL",
                        "normalType": "AFD",
                        "secondIdentifier": "ACCOMMODATION_FARE_DISCOUNT",
                        "amount": discount_amount,
                        "currency": guesty_currency.name,
                        "title": "Fare Accommodation Discount",
                    }
                )

        cleaning_line = self.sale_order_id.order_line.filtered(
            lambda s: s.product_id.id == backend.cleaning_product_id.id
        )

        fare_cleaning = 0.0
        if cleaning_line and reservation_line:
            fare_cleaning = self.sale_order_id.currency_id._convert(
                cleaning_line.price_subtotal,
                guesty_listing_price.currency_id,
                self.sale_order_id.company_id,
                self.sale_order_id.date_order,
            )

        body["money"]["fareCleaning"] = fare_cleaning
        extra_lines = self.sale_order_id.order_line.filtered(
            lambda s: not s.reservation_ok
            and s.id != cleaning_line.id
            and not s.guesty_is_locked
        )

        if extra_lines:
            if "invoiceItems" not in body["money"]:
                body["money"]["invoiceItems"] = []

            for line in extra_lines:
                fare_extra = self.sale_order_id.currency_id._convert(
                    line.price_subtotal,
                    guesty_listing_price.currency_id,
                    self.sale_order_id.company_id,
                    self.sale_order_id.date_order,
                )

                line_payload = {
                    "type": "MANUAL",
                    "title": line.name,
                    "amount": fare_extra,
                    "currency": guesty_currency.name,
                }

                if line.guesty_type:
                    line_payload["type"] = line.guesty_type
                if line.guesty_normal_type:
                    line_payload["normalType"] = line.guesty_normal_type
                if line.guesty_second_identifier:
                    line_payload["secondIdentifier"] = line.guesty_second_identifier

                body["money"]["invoiceItems"].append(line_payload)
        else:
            if "invoiceItems" not in body["money"]:
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

        guesty_currency = None
        for line in guesty_invoice_items:
            guesty_currency = line.get("currency")
            break
        if not guesty_currency:
            guesty_currency = "USD"

        currency_id = (
            self.env["res.currency"].sudo().search([("name", "=", guesty_currency)])
        )

        if not currency_id:
            raise ValidationError(_("Currency: {} Not found").format(guesty_currency))

        context = {"ignore_guesty_push": True, "ignore_overlap": True}
        if status in ["inquiry", "reserved", "confirmed"]:
            if not self.sale_order_id:
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
                        }
                    )
                )

                self.sudo().with_context({"ignore_guesty_push": True}).write(
                    {"sale_order_id": so.id}
                )

            else:
                so = self.sale_order_id

            current_state = so.state
            if current_state == "sale":
                so.with_context(context).write({"state": "draft"})

            self.build_lines(guesty_invoice_items, so, no_nights, currency_id)

            if current_state == "sale" and so.state != "sale":
                so.with_context(context).write({"state": "sale"})

            if status == "reserved":
                self.with_context(context).action_book()

            if status == "confirmed" and so.state == "draft":
                so.with_context(
                    context
                ).action_confirm()  # confirm the SO -> Reservation booked
                self.with_context(context).action_confirm()  # confirm the reservation

        elif status in ["canceled", "declined", "expired", "closed"]:
            cancel_stage_id = self.env.ref(
                "pms_sale.pms_stage_cancelled", raise_if_not_found=False
            )
            if self.sale_order_id and self.sale_order_id.state not in ["cancel"]:
                self.sale_order_id.with_context(context).action_cancel()
            elif cancel_stage_id.id != self.stage_id.id:
                self.with_context(context).action_cancel()

    def build_lines(self, invoice_lines, so, no_nights, currency_id):
        # know if we have the accommodation line in the order

        # lines to preserve after the update
        save_or_update_lines = []
        # Get the accommodation fare adjustment line
        acc_fare_discount_list = [
            a
            for a in invoice_lines
            if a.get("type", str()) == "MANUAL"
            and a.get("normalType", str()) == "AFD"
            and a.get("secondIdentifier", str()) == "ACCOMMODATION_FARE_DISCOUNT"
        ]
        discount_amount = 0
        if len(acc_fare_discount_list) > 0:
            discount_amount = acc_fare_discount_list[0].get("amount")

        order_lines = []
        acc_item_list = [
            a for a in invoice_lines if a.get("type") == "ACCOMMODATION_FARE"
        ]
        if len(acc_item_list) > 0:
            acc_item_line = acc_item_list[0]

            reservation_type = self.property_id.reservation_ids.filtered(
                lambda s: s.is_guesty_price
            )

            if not reservation_type and len(self.property_id.reservation_ids) > 0:
                reservation_type = self.property_id.reservation_ids[0]

            if not reservation_type:
                raise ValidationError(_("Missing guesty reservation type"))

            line_amount = acc_item_line.get("amount")
            line_amount = float(line_amount)

            discount_percent = abs(discount_amount / line_amount * 100.0)
            line_price_unit = line_amount / no_nights
            line_payload = {
                "product_id": reservation_type.product_id.id,
                "name": reservation_type.display_name,
                "product_uom_qty": no_nights,
                "price_unit": currency_id._convert(
                    line_price_unit,
                    so.currency_id,
                    so.company_id,
                    so.date_order,
                ),
                "discount": discount_percent,
                "property_id": self.property_id.id,
                "reservation_id": reservation_type.id,
                "pms_reservation_id": self.id,
                "start": self.start,
                "stop": self.stop,
                "no_of_guests": 1,  # Todo: Set correct number of guests
            }

            acc_line = so.order_line.filtered(lambda s: s.reservation_ok)
            if acc_line:
                save_or_update_lines.append(acc_line.id)
                order_lines.append((1, acc_line.id, line_payload))
            else:
                order_lines.append((0, False, line_payload))

        # remove the lines are not the accommodation one
        backend = self.env.company.guesty_backend_id
        for item in invoice_lines:
            if (
                item.get("type", str()) == "MANUAL"
                and item.get("normalType", str()) == "AFD"
                and item.get("secondIdentifier", str()) == "ACCOMMODATION_FARE_DISCOUNT"
            ):
                # Ignore accommodation discount,
                # will be added as a discount in the accommodation line
                continue
            if item.get("type") in ["TAX", "CITY_TAX", "ACCOMMODATION_FARE"]:
                # Ignore the accommodation fare and taxes, will be added in another process
                continue
            elif item.get("type") == "CLEANING_FEE":
                if item.get("amount", 0.0) <= 0.01:
                    continue

                payload = {
                    "product_id": backend.sudo().cleaning_product_id.id,
                    "name": backend.sudo().cleaning_product_id.name,
                    "product_uom_qty": 1,
                    "price_unit": currency_id._convert(
                        item.get("amount", 0.0),
                        so.currency_id,
                        so.company_id,
                        so.date_order,
                    ),
                    "guesty_type": item.get("type"),
                    "guesty_normal_type": item.get("normalType"),
                    "guesty_second_identifier": item.get("secondIdentifier"),
                }

                cleaning_fee_line = so.order_line.filtered(
                    lambda s: s.guesty_type == "CLEANING_FEE"
                )
                if cleaning_fee_line:
                    save_or_update_lines.append(cleaning_fee_line.id)
                    order_lines.append((1, cleaning_fee_line.id, payload))
                else:
                    order_lines.append(
                        (
                            0,
                            False,
                            payload,
                        )
                    )
            else:
                line_amount = item.get("amount")
                line_amount = float(line_amount)

                payload = {
                    "guesty_is_locked": item.get("isLocked") or False,
                    "guesty_type": item.get("type"),
                    "guesty_normal_type": item.get("normalType"),
                    "guesty_second_identifier": item.get("secondIdentifier"),
                    "product_id": backend.sudo().extra_product_id.id,
                    "name": item.get("title"),
                    "product_uom_qty": 1,
                    "price_unit": currency_id._convert(
                        line_amount,
                        so.currency_id,
                        so.company_id,
                        so.date_order,
                    ),
                }

                extra_line_obj = so.order_line.filtered(
                    lambda s: s.id not in save_or_update_lines
                    and s.guesty_type == item.get("type", str())
                    and s.guesty_normal_type == item.get("normalType", str())
                    and s.guesty_second_identifier
                    == item.get("secondIdentifier", str())
                )

                if extra_line_obj:
                    extra_line_obj = extra_line_obj[0]
                    save_or_update_lines.append(extra_line_obj.id)
                    order_lines.append((1, extra_line_obj.id, payload))
                else:
                    order_lines.append(
                        (
                            0,
                            False,
                            payload,
                        )
                    )

        context = {"ignore_guesty_push": True}
        to_delete = so.order_line.filtered(lambda s: s.id not in save_or_update_lines)
        to_delete.with_context(context).unlink()
        so.with_context(context).write({"order_line": order_lines})

    def action_view_guesty_reservation(self):
        if self.guesty_id:
            url = "{}/reservations/{}/summary".format(
                self.env.company.guesty_backend_id.base_url, self.guesty_id
            )
            return {"type": "ir.actions.act_url", "url": url, "target": "new"}
        else:
            raise UserError(_("Unable to load external url"))
