# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from odoo import http
from odoo.http import request

from odoo.addons.website.controllers.main import QueryURL

from .booking_engine_parser import BookingEngineParser, ParserError

logger = logging.getLogger(__name__)


class RoomController(http.Controller):
    @http.route(
        ["/ebooking/rooms"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def rooms(self, **post):
        errors = []

        if "order" not in post:
            post["order"] = "name asc"

        be_parser = BookingEngineParser(request.env, request.session)
        daterange_error = (
            be_parser.data.get("start_date")
            and be_parser.data.get("end_date")
            and (
                be_parser.data.get("start_date") != post.get("start_date")
                or be_parser.data.get("end_date") != post.get("end_date")
            )
        )

        availability_results = request.env["pms.folio.availability.wizard"]
        if not daterange_error:
            try:
                be_parser.set_daterange(post.get("start_date"), post.get("end_date"))
            except ParserError as e:
                logger.debug(e)
                errors.append(e.usr_msg)

            if not errors:
                try:
                    booking_engine = be_parser.parse()
                except ParserError as e:
                    logger.debug(e)
                    errors.append(e.usr_msg)
                else:
                    availability_results = booking_engine.availability_results

        # Change num_rooms_selected in order to compute price_total for
        # the given daterange, this should not be persisted in session
        for availability_result in availability_results:
            availability_result.num_rooms_selected.value = 1

        sorted_availability_results = self._sort_availability_results(
            availability_results, post.get("order")
        )
        url_generator = QueryURL(
            "/ebooking/rooms",
            order=post.get("order"),
            start_date=be_parser.data.get("start_date"),
            end_date=be_parser.data.get("end_date"),
        )
        values = {
            "url_generator": url_generator,
            "start_date": be_parser.data.get("start_date"),
            "end_date": be_parser.data.get("end_date"),
            "daterange_error": daterange_error,
            "availability_results": sorted_availability_results,
            "errors": errors,
        }

        return request.render("pms_website_sale.pms_room_type_list", values)

    @http.route(
        ["/ebooking/room/<int:room_type_id>"],
        type="http",
        auth="public",
        website=True,
    )
    def room_page(
        self,
        room_type_id,
    ):
        # TODO raise NotFound if not accessible from current website (or if
        #  not published).
        room_type = request.env["pms.room.type"].sudo().browse(room_type_id)
        values = {
            "room_type": room_type,
        }
        return request.render("pms_website_sale.pms_room_type_page", values)

    def _sort_availability_results(self, records, order):
        """Return sorted list of result based on order"""
        key, *direction = order.split(" ")
        key_functions = {
            "name": lambda r: r.room_type_id.name,
            "list_price": lambda r: r.price_per_room,
        }
        key_function = key_functions.get(key, key_functions["name"])

        if direction:
            reverse = direction.pop() == "desc"
        else:
            reverse = False

        return records.sorted(
            key=key_function,
            reverse=reverse,
        )
