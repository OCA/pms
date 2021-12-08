# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import logging

import pytz

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_log = logging.getLogger(__name__)

GUESTY_LISTING_TYPES = ["Private room", "Entire home/apt", "Shared room"]

ODOO_LISTING_TYPES = ["private_room", "entire_home", "shared_room"]

GUESTY_TO_ODOO_LISTING_TYPES = dict(zip(GUESTY_LISTING_TYPES, ODOO_LISTING_TYPES))
ODOO_TO_GUESTY_LISTING_TYPES = dict(zip(ODOO_LISTING_TYPES, GUESTY_LISTING_TYPES))


class PmsProperty(models.Model):
    _inherit = "pms.property"

    guesty_id = fields.Char(copy=False)
    calendar_ids = fields.One2many("pms.guesty.calendar", "property_id")

    def action_guesty_push_property(self):
        self.with_delay().guesty_push_property()

    def guesty_push_property(self):
        backend = self.env.company.guesty_backend_id

        # Guesty use a specific format for address, and autofill the other address fields
        address = "{}, {}, {}, {}, {}, {}".format(
            self.street,
            self.street2,
            self.city,
            self.zip,
            self.state_id.code,
            self.state_id.name,
        )

        body = {"nickname": self.name, "address": {"full": address}}

        guesty_price = self.reservation_ids.filtered(lambda s: s.is_guesty_price)
        if guesty_price:
            body["prices"] = {
                "currency": guesty_price.product_id.currency_id.name,
                "basePrice": guesty_price.price,
            }

        if backend.cleaning_product_id:
            if "prices" not in body:
                body["prices"] = dict()
            body["prices"]["cleaningFee"] = backend.cleaning_product_id.lst_price
            body["financials"] = {
                "cleaningFee": {
                    "value": {
                        "formula": backend.cleaning_product_id.lst_price,
                        "multiplier": "PER_STAY",
                        "valueType": "FIXED",
                    }
                }
            }

        if self.guesty_id:
            success, result = backend.call_put_request(
                url_path="listings/{}".format(self.guesty_id), body=body
            )
        else:
            success, result = backend.call_post_request(url_path="listings", body=body)

        if success and not self.guesty_id:
            guesty_id = result.get("id")
            self.write({"guesty_id": guesty_id})

    def guesty_pull_listing(self, backend, payload):
        _id, property_data = self.sudo().guesty_parse_listing(payload, backend)
        property_id = self.sudo().search([("guesty_id", "=", _id)], limit=1)

        if not property_id:
            self.env["pms.property"].sudo().create(property_data)
        else:
            property_id.sudo().write(property_data)

        return True

    def guesty_parse_listing(self, payload, backend):
        guesty_id = payload.get("id")
        property_data = {
            "guesty_id": guesty_id,
            "name": payload.get("nickname"),
            "owner_id": 1,  # todo: Change and define a default owner
        }
        listing_type = payload.get("roomType")
        if listing_type and listing_type in GUESTY_TO_ODOO_LISTING_TYPES:
            property_data["listing_type"] = GUESTY_TO_ODOO_LISTING_TYPES[listing_type]

        guesty_address = payload.get("address", {})

        street = guesty_address.get("street")
        if street:
            property_data["street"] = street
        city = guesty_address.get("city")
        if city:
            property_data["city"] = city
        zip_code = guesty_address.get("zipcode")
        if zip_code:
            property_data["zip"] = zip_code
        country = guesty_address.get("country")
        if country:
            if country.lower() in ["mexico", "méxico"]:
                res_country = self.env.ref("base.mx", raise_if_not_found=False)
            else:
                res_country = self.env["res.country"].search(
                    [("name", "=", country)], limit=1
                )

            if res_country:
                property_data["country_id"] = res_country.id

        listing_timezone = payload.get("timezone")
        if listing_timezone:
            property_data["tz"] = listing_timezone

        # parse string time to float
        for guesty_time, odoo_field in [
            ("defaultCheckInTime", "checkin"),
            ("defaultCheckOutTime", "checkout"),
        ]:
            str_guesty_time = payload.get(guesty_time)
            if str_guesty_time:
                obj_time = datetime.datetime.strptime(str_guesty_time, "%H:%M")
                delta_time = obj_time - datetime.datetime(1900, 1, 1)
                seconds = delta_time.total_seconds()
                time_seconds = seconds / 3600
                property_data[odoo_field] = time_seconds

        # Guests
        no_guests = payload.get("accommodates", 1)
        property_data["no_of_guests"] = no_guests

        # Terms
        min_nights = payload.get("terms", {}).get("minNights", 1)
        max_nights = payload.get("terms", {}).get("maxNights", 30)
        property_data["min_nights"] = min_nights
        property_data["max_nights"] = max_nights

        return guesty_id, property_data

    def property_get_price(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Calendar Wizard",
            "res_model": "pms.guesty.calendar.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_property_id": self.id},
        }

    def guesty_get_calendars(self, start, stop):
        utc = pytz.UTC
        tz = pytz.timezone(self.tz or "America/Mexico_City")

        start_localized = utc.localize(start).astimezone(tz)
        stop_localized = utc.localize(stop).astimezone(tz)

        backend = self.env.company.guesty_backend_id
        success, results = backend.call_get_request(
            url_path="listings/{}/calendar".format(self.guesty_id),
            params={
                "fields": ", ".join(["status"]),
                "from": start_localized.strftime("%Y-%m-%d"),
                "to": stop_localized.strftime("%Y-%m-%d"),
            },
        )

        if not success:
            raise ValidationError(_("Unable to get calendar information"))

        return results

    def odoo_get_calendars(self, start, stop):
        utc = pytz.UTC
        tz = pytz.timezone(self.tz or "America/Mexico_City")

        start_localized = utc.localize(start).astimezone(tz)
        stop_localized = utc.localize(stop).astimezone(tz)

        calendars = (
            self.env["pms.guesty.calendar"]
            .sudo()
            .search(
                [
                    ("listing_date", ">=", start_localized.date()),
                    ("listing_date", "<=", stop_localized.date()),
                ]
            )
        )

        return calendars
