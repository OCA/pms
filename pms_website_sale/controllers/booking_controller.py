# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later


from datetime import date, timedelta

from odoo import http
from odoo.fields import Date
from odoo.http import request


class BookingEngineParser:
    def __init__(self, env):
        self.env = env
        self.booking_engine = None
        self.post_data = None

    def _get_booking_engine_vals(self):

        start_date = date.fromisoformat(self.post_data["start_date"])
        end_date = date.fromisoformat(self.post_data["end_date"])

        partner = self.post_data.get("partner_id", False)
        if not partner:
            partner = self.env.ref("base.public_partner")

        online_channel = self.env.ref("pms_website_sale.online_channel")

        values = {
            "partner_id": partner.id,
            "start_date": start_date,
            "end_date": end_date,
            "channel_type_id": online_channel.id,
        }
        return values

    def _populate_availability_results(self):
        rooms_request = self.post_data.get("rooms_request", [])
        for room in rooms_request:
            room_availability = self.booking_engine.availability_results.filtered(
                lambda ar: ar.room_type_id.id == room["room_type_id"]
            )

            if not room_availability:
                raise ValueError(
                    "No room type for (%s, %s)"
                    % (room["room_type_id"], room["room_name"])
                )

            if room["quantity"] > room_availability.num_rooms_available:
                raise ValueError(
                    "Not enough rooms available"
                    " for (%s, %s)" % (room["room_type_id"], room["room_name"])
                )

            room_availability.value_num_rooms_selected = room["quantity"]

    def parse(self, post_data):
        self.post_data = post_data
        values = self._get_booking_engine_vals()
        self.booking_engine = (
            self.env["pms.booking.engine"]
            .sudo()  # fixme think this sudo
            .create(values)
        )
        self._populate_availability_results()
        return self.booking_engine


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
