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
        "rooms_requests": [
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
        methods=["GET", "POST"],
    )
    def booking(self, **post):
        be_parser = BookingEngineParser(request.env, request.session)

        if request.httprequest.method == "POST":
            if post.get("delete"):
                # TODO: delete lines
                pass
            else:
                try:
                    # Set daterange if it has not been set previously
                    be_parser.set_daterange(
                        post.get("start_date"), post.get("end_date"), overwrite=False
                    )
                    be_parser.add_room_request(
                        post.get("room_type_id"),
                        post.get("quantity"),
                        post.get("start_date"),
                        post.get("end_date"),
                    )
                except ValueError as e:
                    raise e
                be_parser.save()
        try:
            booking_engine = be_parser.parse()
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
