# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import logging

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_log = logging.getLogger(__name__)

GUESTY_DEFAULT_PAYLOAD = {
    "source": "odoo",
    "listingId": None,
    "guest": {
        "_id": None,
        "fullName": None,
        "email": None,
        "phone": None,
    },
    "checkInDateLocalized": None,
    "checkOutDateLocalized": None,
    "plannedArrival": None,
    "plannedDeparture": None,
    "money": {
        "fareAccommodation": 0.0,
        "fareCleaning": 0.0,
        "currency": "USD",
        "invoiceItems": [],
    },
}


class PmsReservation(models.Model):
    _inherit = "pms.reservation"

    guesty_id = fields.Char(copy=False)
    guesty_last_updated_date = fields.Datetime()
    guesty_reservation_id = fields.Many2one("pms.guesty.reservation", copy=False)
    pms_source_id = fields.Selection(
        [("odoo", "Odoo"), ("guesty", "Guesty")], default="odoo"
    )

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
        # ignore overlaps for reservations, it was manager by guesty.
        return True

    @api.model
    def create(self, values):
        return super().create(values)

    def write(self, values):
        if "guesty_id" in values and not self.pms_source_id:
            values["pms_source_id"] = (
                self.env["pms.guesty.reservation"]
                .create({"uuid": values["guesty_id"], "state": "ND"})
                .id
            )
        return super().write(values)

    def action_draft(self):
        ignore_push_event = self.env.context.get("ignore_push_event", False)
        company = self.property_id.company_id or self.env.company
        if self.stage_id.id != self.env.company.guesty_backend_id.stage_inquiry_id.id:
            self.write(
                {"stage_id": self.env.company.guesty_backend_id.stage_inquiry_id.id}
            )

            if company.guesty_backend_id and self.guesty_id and not ignore_push_event:
                rs = self.guesty_push_reservation_draft()
                self.message_post(
                    body=_(
                        "Reservation was updated on guesty :: {}".format(rs["status"])
                    )
                )

    def action_book(self):
        ignore_push_event = self.env.context.get("ignore_push_event", False)

        _log.info("Ignore push events: {}".format(ignore_push_event))
        _log.info(self.stage_id)
        _log.info(self.env.company.guesty_backend_id)

        if self.stage_id.id in [
            self.env.company.guesty_backend_id.stage_reserved_id.id,
            self.env.company.guesty_backend_id.stage_confirmed_id.id,
        ]:
            return None

        res = super(PmsReservation, self).action_book()
        if self.env.company.guesty_backend_id and not ignore_push_event:
            self.guesty_check_availability()
            # Send to Guesty
            self.guesty_push_reservation_reserve()
        return res

    def action_confirm(self):
        # If the reservation is already confirmed, we don´t do more
        if self.stage_id.id == self.env.company.guesty_backend_id.stage_confirmed_id.id:
            return None

        ignore_push_event = self.env.context.get("ignore_push_event", False)

        res = super(PmsReservation, self).action_confirm()

        if self.env.company.guesty_backend_id and not ignore_push_event:
            status = self.guesty_get_status()
            if status not in ["inquiry", "reserved"]:
                raise ValidationError(
                    _("Unable to confirm reservation, status is {}".format(status))
                )
            # Send to guesty
            self.guesty_push_reservation_confirm()
        return res

    def action_cancel(self):
        ignore_push_event = self.env.context.get("ignore_push_event", False)

        res = super(PmsReservation, self).action_cancel()
        company = self.property_id.company_id or self.env.company
        _log.info("Cancelling reservation with company {}".format(company))

        if company.guesty_backend_id and self.guesty_id and not ignore_push_event:
            self.guesty_push_reservation_cancel()
        else:
            _log.info("Ignoring send cancel evento to guesty")
        return res

    def action_cancel_sale_order(self):
        if self.sale_order_id:
            _log.info("Reservation has a sale order")
            if self.sale_order_id.state != "cancel":
                _log.info("Cancelling sale order {}".format(self.sale_order_id.name))
                active_reservations = self.sale_order_id.sale_get_active_reservation()
                if len(active_reservations) == 0:
                    self.sale_order_id.action_cancel(
                        ignore_push_event=True, cancel_reservation=False
                    )

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
        success, result = self.guesty_push_reservation(
            default_status="canceled",
            canceled_by=self.env.user.name,
            include_body=False,
        )

        if not success:
            self.message_post(body=_("Reservations cannot be canceled"))
            raise UserError(_("Unable to cancel reservation"))

        self.message_post(body=_("Reservation cancelled successfully on guesty!"))

    def guesty_push_reservation_reserve(self):
        success, result = self.guesty_push_reservation(default_status="reserved")
        if success:
            self.message_post(body=_("Reservation reserved successfully on guesty!"))
        else:
            _log.error(result)
            raise ValidationError(_("Unable to reserve reservation"))

    def guesty_push_reservation_confirm(self):
        success, result = self.guesty_push_reservation(default_status="confirmed")

        if not success:
            raise UserError(_("Unable to confirm reservation : {}".format(result)))

        self.message_post(body=_("Reservation confirmed successfully on guesty!"))

    def guesty_push_reservation_draft(self):
        success, result = self.guesty_push_reservation(default_status="inquiry")
        if not success:
            raise UserError(_("Unable to reset reservation : {}".format(result)))

        return result

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

    def guesty_push_reservation(
        self, default_status=None, canceled_by=None, include_body=True
    ):
        company = self.property_id.company_id or self.env.company
        backend = company.guesty_backend_id
        if not backend:
            raise ValidationError(_("No backend defined"))

        # create a reservation on guesty
        if include_body:
            body = self.parse_push_reservation_data(backend)
        else:
            body = {}

        if default_status:
            body["status"] = default_status

        if canceled_by:
            body["canceledBy"] = canceled_by

        if self.sale_order_id:
            if not self.partner_id.guesty_ids:
                customer = backend.guesty_search_create_customer(self.partner_id)
                body["guestId"] = customer.guesty_id
            else:
                for guest in self.partner_id.guesty_ids:
                    guest.guesty_push_update()
                    body["guestId"] = guest.guesty_id
                    break

            if self.guesty_id:
                _log.info(body)
                success, res = backend.call_put_request(
                    url_path="reservations/{}".format(self.guesty_id), body=body
                )
            else:
                success, res = backend.call_post_request(
                    url_path="reservations", body=body
                )
                if success:
                    guesty_id = res.get("_id")
                    self.write({"guesty_id": guesty_id})

            if not success:
                if "Invalid dates" in res:
                    raise ValidationError(
                        _("Invalid dates {} - {}".format(self.start, self.stop))
                    )
                raise UserError(_("Unable to send to guesty") + ": " + str(res))
            return success, res
        else:
            raise ValidationError(_("No sale order linked to reservation"))

    def guesty_pull_reservation(self, reservation_info, event_name):
        guesty_listing_id = reservation_info["listingId"]
        _log.info("Pulling reservation for listing {}".format(guesty_listing_id))

        listing_obj = self.env["pms.guesty.listing"].search(
            [("external_id", "=", guesty_listing_id)]
        )
        property_id = None
        if listing_obj:
            property_id = self.env["pms.property"].search(
                [("guesty_listing_ids.id", "=", listing_obj.id)]
            )

        if not property_id:
            property_id = (
                self.env["pms.property"]
                .sudo()
                .search([("guesty_id", "=", guesty_listing_id)], limit=1)
            )

        _log.info("Property {}".format(property_id.ref or property_id.id))

        if not property_id:
            raise ValidationError(_("Property not found"))

        company_id = property_id.company_id or self.env.company
        if not company_id:
            raise ValidationError(
                _("Company not found on listing {}".format(guesty_listing_id))
            )

        backend = company_id.guesty_backend_id
        if not backend:
            raise ValidationError(_("No backend defined"))

        success, reservation_data = backend.sudo().call_get_request(
            url_path="reservations/{}".format(reservation_info["_id"]),
            params={
                "fields": " ".join(
                    [
                        "status",
                        "checkIn",
                        "checkOut",
                        "listingId",
                        "guestId",
                        "listing.nickname",
                        "createdAt",
                        "lastUpdatedAt",
                        "money",
                        "nightsCount",
                    ]
                )
            },
        )

        if not success:
            raise ValidationError(_("Unable to retrieve reservation"))

        # validate the reservation already exists
        _id, reservation = self.sudo().guesty_parse_reservation(
            reservation_data, backend
        )

        reservation["property_id"] = property_id.id

        reservation_id = (
            self.env["pms.reservation"].sudo().search([("guesty_id", "=", _id)])
        )

        if reservation_id.exists():
            reservation_id.write(reservation)
        else:
            reservation["pms_source_id"] = "guesty"
            reservation_id = self.env["pms.reservation"].sudo().create(reservation)

        if reservation_data["status"] in ["canceled", "declined", "expired", "closed"]:
            if reservation_id.stage_id.id != backend.stage_canceled_id.id:
                _log.info("Canceling reservation {}".format(reservation_id.id))
                reservation_id.sudo().with_context(
                    ignore_push_event=True
                ).action_cancel()
                reservation_id.action_cancel_sale_order()
            else:
                _log.info("Reservation {} already canceled".format(reservation_id.id))
        elif reservation_data["status"] == "inquiry":
            if reservation_id.stage_id.id != backend.stage_inquiry_id.id:
                reservation_id.sudo().with_context(
                    ignore_push_event=True
                ).action_draft()
            else:
                _log.info("Reservation {} already inquiry".format(reservation_id.id))
        elif reservation_data["status"] in ["reserved"]:
            if reservation_id.stage_id.id != backend.stage_reserved_id.id:
                _log.info("Reservation {} reserved".format(reservation_id.id))
                reservation_id.sudo().with_context(ignore_push_event=True).action_book()
            else:
                _log.info("Reservation {} already reserved".format(reservation_id.id))
        elif reservation_data["status"] in ["confirmed"]:
            if reservation_id.stage_id.id != backend.stage_confirmed_id.id:
                _log.info("Reservation {} confirmed".format(reservation_id.id))
                reservation_id.sudo().with_context(
                    ignore_push_event=True
                ).action_confirm()
            else:
                _log.info("Reservation {} already confirmed".format(reservation_id.id))
            try:
                if reservation_id.pms_source_id != "odoo":
                    reservation_id.build_so_from_reservation(reservation_data)
            except Exception as ex:
                _log.error(ex)

        return reservation_id

    def guesty_parse_reservation(self, reservation, backend):
        guesty_id = reservation.get("_id")
        listing_id = reservation.get("listingId")
        check_in = reservation.get("checkIn")
        check_out = reservation.get("checkOut")
        guest_id = reservation.get("guestId")
        guesty_last_updated_date = reservation.get("lastUpdatedAt")

        property_id = self.env["pms.property"].search(
            [("guesty_id", "=", listing_id)], limit=1
        )

        if not property_id.exists():
            raise ValidationError(_("Listing: {} does not exist".format(listing_id)))

        pms_guest = backend.sudo().guesty_search_pull_customer(guest_id)

        check_in_date_part = check_in[0:10]
        check_out_date_part = check_out[0:10]

        checkin_date_date = datetime.datetime.strptime(check_in_date_part, "%Y-%m-%d")
        checkout_date_date = datetime.datetime.strptime(check_out_date_part, "%Y-%m-%d")

        tz = pytz.timezone(property_id.tz)

        checkin_date_date = tz.localize(checkin_date_date).astimezone(pytz.UTC)
        checkout_date_date = tz.localize(checkout_date_date).astimezone(pytz.UTC)

        localize_ci = False
        localize_co = False

        if "plannedArrival" in reservation:
            check_in_time_part = reservation["plannedArrival"]
            _log.info(check_in_time_part)
            checkin_time_time = datetime.datetime.strptime(
                check_in_time_part, "%H:%M"
            ).time()
            localize_ci = True
        else:
            check_in_time_part = check_in[11:19]
            checkin_time_time = datetime.datetime.strptime(
                check_in_time_part, "%H:%M:%S"
            ).time()

        if "plannedDeparture" in reservation:
            check_out_time_part = reservation["plannedDeparture"]
            _log.info(check_out_time_part)
            checkout_time_time = datetime.datetime.strptime(
                check_out_time_part, "%H:%M"
            ).time()
            localize_co = True
        else:
            check_out_time_part = check_out[11:19]
            checkout_time_time = datetime.datetime.strptime(
                check_out_time_part, "%H:%M:%S"
            ).time()

        check_in_time = datetime.datetime.combine(checkin_date_date, checkin_time_time)
        check_out_time = datetime.datetime.combine(
            checkout_date_date, checkout_time_time
        )

        if localize_ci:
            check_in_time = (
                tz.localize(check_in_time).astimezone(pytz.UTC).replace(tzinfo=None)
            )
        if localize_co:
            check_out_time = (
                tz.localize(check_out_time).astimezone(pytz.UTC).replace(tzinfo=None)
            )

        guesty_last_updated_time = datetime.datetime.strptime(
            guesty_last_updated_date[0:19], "%Y-%m-%dT%H:%M:%S"
        )

        return guesty_id, {
            "guesty_id": guesty_id,
            "property_id": property_id.id,
            "start": check_in_time,
            "stop": check_out_time,
            "partner_id": pms_guest.partner_id.id,
            "guesty_last_updated_date": guesty_last_updated_time,
        }

    def parse_push_reservation_data(self, backend):
        guesty_listing_price = self.property_id.reservation_ids.filtered(
            lambda s: s.is_guesty_price
        )

        # customer = backend.guesty_search_create_customer(self.partner_id)

        utc = pytz.UTC
        tz = pytz.timezone(self.property_id.tz or backend.timezone)
        checkin_localized = utc.localize(self.start).astimezone(tz)
        checkout_localized = utc.localize(self.stop).astimezone(tz)

        guesty_currency = (
            guesty_listing_price.currency_id
            or backend.currency_id
            or self.env.company.currency_id
        )

        body = {
            "listingId": self.property_id.guesty_id,
            "checkInDateLocalized": checkin_localized.strftime("%Y-%m-%d"),
            "checkOutDateLocalized": checkout_localized.strftime("%Y-%m-%d"),
            "plannedArrival": checkin_localized.strftime("%H:%M"),
            "plannedDeparture": checkout_localized.strftime("%H:%M"),
            "money": {"invoiceItems": []},
        }

        reservation_line = self.sale_order_id.order_line.filtered(
            lambda s: s.reservation_ok
        )
        if reservation_line:
            body["money"] = GUESTY_DEFAULT_PAYLOAD["money"].copy()
            if backend.enable_guesty_discount:
                fare_acc_amount = (
                    reservation_line.price_unit * reservation_line.product_uom_qty
                )

                if reservation_line.discount != 0:
                    discount_amount = fare_acc_amount - (
                        fare_acc_amount * (1.0 - reservation_line.discount / 100.0)
                    )

                    discount_amount = self.sale_order_id.currency_id._convert(
                        discount_amount,
                        guesty_currency,
                        self.sale_order_id.company_id,
                        self.sale_order_id.date_order,
                    )

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
            else:
                _log.info("================ WITHOUT DISCOUNT ================")
                fare_acc_amount = reservation_line.price_subtotal

            fare_accommodation = self.sale_order_id.currency_id._convert(
                fare_acc_amount,
                guesty_currency,
                self.sale_order_id.company_id,
                self.sale_order_id.date_order,
            )

            body["money"] = {
                "fareAccommodation": fare_accommodation,
                "currency": guesty_currency.name,
            }

        cleaning_line = self.sale_order_id.order_line.filtered(
            lambda s: s.product_id.id == backend.cleaning_product_id.id
        )

        fare_cleaning = 0.0
        if cleaning_line and reservation_line:
            fare_cleaning = self.sale_order_id.currency_id._convert(
                cleaning_line.price_subtotal,
                guesty_currency,
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

        # Custom fields
        for custom_field_id in backend.custom_field_ids:
            if custom_field_id.name == "company" and self.partner_id.parent_id:
                body["customFields"] = [
                    {
                        "fieldId": custom_field_id.guesty_custom_field_id.external_id,
                        "value": self.partner_id.parent_id.name,
                    }
                ]

        if "notes" not in body:
            body["notes"] = {}

        if "other" not in body["notes"]:
            body["notes"]["other"] = self.user_id.name

        return body

    def build_so_from_reservation(self, reservation_data):
        _log.info(reservation_data)
        guesty_currency = reservation_data["money"]["currency"]
        _log.info("Saving in currency %s", guesty_currency)

        currency_id = (
            self.env["res.currency"].sudo().search([("name", "=", guesty_currency)])
        )

        if not currency_id:
            raise ValidationError(_("Currency: {} Not found").format(guesty_currency))

        created_at = datetime.datetime.strptime(
            reservation_data["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        so_payload = {
            "partner_id": self.partner_id.id,
            "date_order": created_at,
        }

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

            so_payload["pricelist_id"] = price_list.id
            so = self.env["sale.order"].sudo().create(so_payload)

            self.sudo().write({"sale_order_id": so.id})

        else:
            so = self.sale_order_id
            so.write(so_payload)

        if so.state not in ["draft", "sent", "approved"]:
            raise ValidationError(
                _("Unable to build a sale order, status is {}").format(so.state)
            )

        guesty_invoice_items = reservation_data["money"]["invoiceItems"]
        no_nights = reservation_data["nightsCount"]
        self.build_lines(guesty_invoice_items, so, no_nights, currency_id)
        so.action_confirm()

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
        company = self.company_id or self.env.company
        backend = company.guesty_backend_id
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
