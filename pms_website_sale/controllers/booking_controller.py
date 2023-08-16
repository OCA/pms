# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later


from datetime import timedelta

from odoo import http
from odoo.fields import Date
from odoo.http import request

from .booking_engine_parser import BookingEngineParser


class BookingEngineController(http.Controller):
    @http.route(
        ["/booking"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],  # fixme
    )
    def booking(self, **post):
        # dummy data
        today = Date.today()
        single = request.env.ref("pms.pms_room_type_single").sudo()
        double = request.env.ref("pms.pms_room_type_double").sudo()
        post = {
            "partner_id": False,
            "start_date": Date.to_string(today),
            "end_date": Date.to_string(today + timedelta(days=3)),
            "channel_type_id": False,
            "rooms_request": [
                {"room_type_id": single.id, "room_name": single.name, "quantity": 1},
                {"room_type_id": double.id, "room_name": double.name, "quantity": 2},
            ],
        }

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
