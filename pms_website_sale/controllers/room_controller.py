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
        ["/rooms"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def rooms(
        self,
        **post,
    ):
        errors = []

        if "order" not in post:
            post["order"] = "name asc"

        # FIXME: Do we need to take daterange from the session if not
        # present in the url parameters ? But this imply to change the
        # mechanism of setting the daterange on the rooms page, because
        # the mechanism to delete the daterange selection will no longer
        # work.
        be_parser = BookingEngineParser(request.env, {})
        try:
            be_parser.set_daterange(post.get("start_date"), post.get("end_date"))
        except ParserError as e:
            logger.error(e)
            errors.append(e.usr_msg)

        try:
            booking_engine = be_parser.parse()
        except ParserError as e:
            logger.error(e)
            errors.append(e.usr_msg)

        sorted_availability_results = self._sort_availability_results(
            booking_engine.availability_results, post.get("order")
        )
        url_generator = QueryURL(
            "/rooms",
            order=post.get("order"),
            start_date=post.get("start_date"),
            end_date=post.get("end_date"),
        )
        values = {
            "url_generator": url_generator,
            "start_date": post.get("start_date"),
            "end_date": post.get("end_date"),
            "availability_results": sorted_availability_results,
            "errors": errors,
        }

        return request.render("pms_website_sale.pms_room_type_list", values)

    @http.route(
        ['/room/<model("pms.room.type"):room_type>'],
        type="http",
        auth="public",
        website=True,
    )
    def room_page(
        self,
        room_type,
    ):
        # TODO raise NotFound if not accessible from current website (or if
        #  not published).
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
