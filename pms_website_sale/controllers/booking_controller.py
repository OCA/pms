# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
from datetime import timedelta

from odoo import http
from odoo.fields import Date
from odoo.http import request

from .booking_engine_parser import BookingEngineParser, ParserError

logger = logging.getLogger(__name__)


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
        errors = []
        be_parser = BookingEngineParser(request.env, request.session)

        if request.httprequest.method == "POST":
            if "delete" in post:
                try:
                    be_parser.del_room_request(post.get("delete"))
                except ParserError as e:
                    logger.error(e)
                    errors.append(e.usr_msg)
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
                except ParserError as e:
                    logger.error(e)
                    errors.append(e.usr_msg)
            be_parser.save()
        try:
            booking_engine = be_parser.parse()
        except KeyError as e:
            # todo return a nicer error
            # FIXME: why this type of error occurs ?
            raise e
        except ParserError as e:
            logger.error(e)
            errors.append(e.usr_msg)

        values = {
            "booking_engine": booking_engine,
            "errors": errors,
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
        # todo create partner
        post.update(_dummy_request())
        parser = BookingEngineParser(request.env, request.session)
        booking_engine = parser.parse(post)
        values["booking_engine"] = booking_engine
        return request.render("pms_website_sale.pms_booking_payment_page", values)

    @http.route(
        ["/booking/payment"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def booking_payment(self, **post):
        # fixme dummy post
        post.update(_dummy_request())
        partner = request.env.ref("base.partner_demo")
        post["partner_id"] = partner.id
        parser = BookingEngineParser(request.env, request.session)
        booking_engine = parser.parse()

        acquirers = request.env["payment.acquirer"].search(
            [
                ("state", "in", ["enabled", "test"]),
                ("company_id", "=", request.env.company.id),
            ]
        )
        return_url = request.params.get("redirect", "/booking/payment/success")

        values = {
            "booking_engine": booking_engine,
            # 'pms': payment_tokens,
            "acquirers": acquirers,
            "error_message": [post["error"]] if post.get("error") else False,
            "return_url": return_url,
            # 'bootstrap_formatting': True,
            "partner_id": partner.id,
        }

        return request.render("pms_website_sale.pms_booking_payment_page", values)

    @http.route(
        ["/booking/success"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def booking_success(self, **post):
        return request.render("pms_website_sale.pms_booking_success_page")

    @http.route(
        ["/booking/failure"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def booking_failure(self, **post):
        return request.render("pms_website_sale.pms_booking_failure_page")
