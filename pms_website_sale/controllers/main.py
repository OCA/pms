# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from collections import namedtuple
from datetime import datetime

from odoo import http
from odoo.http import request

from odoo.addons.website.controllers.main import QueryURL

# This is a mocked version of AvailabilityResult that we populate when FIXME.
AvailabilityResult = namedtuple("AvailabilityResult", ["room_type_id"])


class WebsiteSale(http.Controller):
    @http.route(
        ["/room"],
        type="http",
        auth="public",
        website=True,
        # Do we need a sitemap?
        # sitemap=?,
    )
    def room(
        self,
        # The commented out arguments are used by website_sale. We may want to
        # also use some of them.
        # page=0,
        # category=None,
        # search="",
        # ppg=False,
        **post,
    ):
        keep = QueryURL(
            "/room",
            # category=category and int(category),
            # search=search,
            order=post.get("order"),
            start_date=post.get("start_date"),
            end_date=post.get("end_date"),
        )
        booking_engine = self._get_booking_engine(post)
        if booking_engine:
            availability_results = booking_engine.availability_results.filtered(
                lambda record: record.room_type_id in self._search_room_types(post)
            ).sorted(
                # FIXME: This is incomplete.
            )
        # No dates provided, ergo no availability_results. Create them
        # ourselves.
        else:
            availability_results = [
                AvailabilityResult(room_type)
                for room_type in self._search_room_types(post)
            ]

        values = {
            "keep": keep,
            "availability_results": availability_results,
        }

        return request.render("pms_website_sale.rooms", values)

    def _get_booking_engine(self, post):
        # TODO: In the future, maybe let's cache the booking engine between
        # requests.
        start_date = post.get("start_date")
        end_date = post.get("end_date")
        if not (start_date and end_date):
            # FIXME: resolve this problem.
            return None
        try:
            # Sanitise user input.
            start_date = datetime.strptime(start_date, r"%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, r"%Y-%m-%d").date()
        except ValueError:
            # FIXME: resolve this problem
            return None
        return request.env["pms.booking.engine"].create(
            {
                "partner_id": request.env.ref("base.public_partner").id,
                "start_date": start_date,
                "end_date": end_date,
                "channel_type_id": request.env.ref(
                    "pms_website_sale.online_channel"
                ).id,
            }
        )

    @http.route(
        ['/room/<model("pms.room.type"):room_type>'],
        type="http",
        auth="public",
        website=True,
        # sitemap=True,
    )
    def room_page(
        self,
        room_type,
        # category="",
        # search="",
        **post,
    ):
        # FIXME: raise NotFound if not accessible from current website (or if
        # not published).
        values = {
            "room_type": room_type,
        }
        return request.render("pms_website_sale.room_page", values)

    def _search_room_types(self, post):
        domain = self._get_search_domain()
        order = self._get_search_order(post)
        return request.env["pms.room.type"].search(domain, order=order)

    def _get_search_domain(self):
        # TODO: Improve this.
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
