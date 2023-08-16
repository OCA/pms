# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later


from datetime import timedelta

from odoo import http
from odoo.fields import Date
from odoo.http import request

from .booking_engine_parser import BookingEngineParser


def _dummy_request():
    # dummy data
    today = Date.today()
    single = request.env.ref("pms.pms_room_type_single").sudo()
    double = request.env.ref("pms.pms_room_type_double").sudo()
    return {
        "partner_id": False,
        "start_date": Date.to_string(today),
        "end_date": Date.to_string(today + timedelta(days=3)),
        "channel_type_id": False,
        "rooms_request": [
            {"room_type_id": single.id, "room_name": single.name, "quantity": 1},
            {"room_type_id": double.id, "room_name": double.name, "quantity": 2},
        ],
    }


class BookingEngineController(http.Controller):
    @http.route(
        ["/booking"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],  # fixme
    )
    def booking(self, **post):
        # fixme dummy post
        post.update(_dummy_request())
        parser = BookingEngineParser(request.env)
        try:
            booking_engine = parser.parse(post)
        except KeyError as e:
            # todo return a nicer error
            raise e
        except ValueError as e:
            # todo return a nicer error
            raise e

        values = {
            "booking_engine": booking_engine,
        }
        return request.render("pms_website_sale.pms_booking_engine_page", values)

    @http.route(
        ["/booking/address"],
        type="http",
        auth="public",
        website=True,
        methods=["GET", "POST"],
    )
    def booking_address(self, **post):
        countries = request.env["res.country"].sudo().search([])
        default_country = request.env.company.country_id
        values = {
            "countries": countries,
            "default_country_id": default_country.id,
        }
        if request.httprequest.method == "GET":
            return request.render("pms_website_sale.pms_booking_address_page", values)

        # fixme dummy post
        post.update(_dummy_request())
        parser = BookingEngineParser(request.env)
        booking_engine = parser.parse(post)
        values["booking_engine"] = booking_engine
        return request.render(
            "pms_website_sale.pms_booking_engine_page", values
        )  # fixme to confirm page
