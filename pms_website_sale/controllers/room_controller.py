# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later


from odoo import http
from odoo.http import request

from odoo.addons.website.controllers.main import QueryURL

from .booking_engine_parser import BookingEngineParser


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
        keep = QueryURL(
            "/rooms",
            order=post.get("order"),
            start_date=post.get("start_date"),
            end_date=post.get("end_date"),
        )
        be_parser = BookingEngineParser(request.env)
        booking_engine = be_parser.parse({})
        values = {
            "keep": keep,
            "availability_results": booking_engine.availability_results,
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

    def _search_room_types(self, post):
        # roke : cf pms_booking_engine.py :
        #   I rely on self.env["pms.room.type"].get_room_types_by_property
        #   what do you think is better ?
        domain = self._get_search_domain()
        order = self._get_search_order(post)
        return request.env["pms.room.type"].search(domain, order=order)

    def _get_search_domain(self):
        # TODO: Improve this or remove
        return [
            # Unlike website_sale, we completely filter out non-published items,
            # meaning that even admin users cannot see greyed out unpublished
            # items. If you want this feature, it shouldn't be too difficult to
            # write.
            ("is_published", "=", True),
        ]

    def _get_search_order(self, post):
        # TODO: Get a better fallback than 'name ASC'. website_sale uses
        # 'website_sequence ASC'
        order = post.get("order") or "name ASC"
        return "%s, id desc" % order
