# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request

_log = logging.getLogger(__name__)


def standardize_request_data(data):
    """
    Standardize the request data to be able to use it in the controller.
    """
    standard_data = {}
    if data.get("reservation") and data.get("event"):
        if data.get("event") in ["reservation.new", "reservation.updated"]:
            standard_data["reservation"] = data.get("reservation")
            standard_data["event"] = data.get("event")
    elif data.get("event") and data.get("event", {}).get("reservation"):
        standard_data["reservation"] = data.get("event").get("reservation")
        standard_data["event"] = "reservation.updated"

    return standard_data["reservation"], standard_data["event"]


class GuestyController(http.Controller):
    def validate_get_company(self, payload):
        company_id = payload.get("company")
        if not company_id:
            raise ValidationError(_("No company was specified"))
        company = request.env["res.company"].browse(company_id)
        if not company:
            raise ValidationError(_("Invalid company"))
        backend = company.guesty_backend_id
        if not backend:
            raise ValidationError(_("No backend was defined"))
        return company, backend

    @http.route(
        "/guesty/reservations_webhook",
        methods=["POST"],
        auth="public",
        csrf=False,
        type="json",
    )
    def reservations_webhook(self, **data):
        reservation_info, event_name = standardize_request_data(request.jsonrequest)
        if event_name not in ["reservation.new", "reservation.updated"]:
            raise ValidationError(_("Invalid event name {}".format(event_name)))

        reservation_model = request.env["pms.guesty.reservation"].sudo()
        reservation_model.with_delay(10).pull_reservation(reservation_info)
        return {"success": True}

    @http.route(
        "/guesty/listing_webhook",
        methods=["POST"],
        auth="public",
        csrf=False,
        type="json",
    )
    def listing_webhook(self):
        data = request.jsonrequest
        if data["event"] == "listing.updated" and "listing" in data:
            request.env["pms.guesty.listing"].sudo().with_delay().guesty_pull_listing(
                data["listing"]
            )
        return {"success": True}

    @http.route(
        "/guesty/webhook/<int:backend_id>",
        methods=["POST"],
        auth="public",
        csrf=False,
        type="json",
    )
    def webhook(self, backend_id):
        connector = request.env["backend.guesty"].sudo().browse(backend_id)
        data = request.jsonrequest
        if data.get("event") == "listing.calendar.updated":
            # do actions for calendars
            request.env["pms.guesty.calendar"].sudo().with_company(
                connector.company_id
            ).with_delay().do_calendar_update(data)
        return True
