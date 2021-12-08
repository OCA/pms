# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import logging

import pytz

from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError

_log = logging.getLogger(__name__)


class PmsGuestyCalendar(models.Model):
    _name = "pms.guesty.calendar"

    listing_id = fields.Char(required=True)
    listing_date = fields.Date(required=True)
    state = fields.Selection(
        [
            ("available", _("Available")),
            ("unavailable", _("Unavailable")),
            ("reserved", _("Reserved")),
            ("booked", _("Booked")),
        ],
        required=True,
    )

    price = fields.Float(required=True)
    currency = fields.Char(required=True)
    note = fields.Text()

    property_id = fields.Many2one("pms.property", required=True)

    _sql_constraints = [
        (
            "unique_listing_date",
            "unique(listing_id, listing_date)",
            "you cannot have dates duplicated by listing",
        )
    ]

    def guesty_pull_calendar(self, backend, property_id, start_date, stop_date):
        success, result = backend.call_get_request(
            url_path="/listings/{}/calendar".format(property_id.guesty_id),
            params={"from": start_date, "to": stop_date},
        )

        if success:
            for record in result:
                calendar_id = self.sudo().search(
                    [
                        ("listing_id", "=", property_id.guesty_id),
                        ("listing_date", "=", record.get("date")),
                    ]
                )

                payload = {
                    "listing_id": property_id.guesty_id,
                    "listing_date": record.get("date"),
                    "state": record.get("status"),
                    "price": record.get("price"),
                    "currency": record.get("currency"),
                    "note": record.get("note"),
                    "property_id": property_id.id,
                }

                if not calendar_id.exists():
                    self.sudo().create(payload)
                else:
                    calendar_id.sudo().write(payload)
        else:
            raise UserError(_("Failed to sync calendars"))

    def compute_price(self, property_id, start_date, end_date, currency):
        """
        Compute the price for a date range based on calendar prices
        :param Model(pms.property) property_id:
        :param Datetime start_date:
        :param Datetime end_date:
        :param str currency:
        :return:
        """
        utc = pytz.UTC
        tz = pytz.timezone(self.property_id.tz or "America/Mexico_City")
        start_date_localized = utc.localize(start_date).astimezone(tz)
        stop_date_localized = utc.localize(end_date).astimezone(tz)

        # remove 1 day because the checkout day is a day after
        real_end_date = stop_date_localized - datetime.timedelta(days=1)
        calendars = self.sudo().search(
            [
                ("property_id", "=", property_id.id),
                ("listing_date", ">=", start_date_localized.date()),
                ("listing_date", "<=", real_end_date.date()),
            ]
        )

        days_len = (stop_date_localized.date() - start_date_localized.date()).days
        if days_len != len(calendars):
            raise ValidationError("Invalid days range")

        for calendar_day in calendars:
            _log.info(calendar_day.listing_date)

        raise ValidationError("Looks fine")
