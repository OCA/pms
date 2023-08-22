# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from lxml.html import fromstring

from odoo.tests.common import HttpCase

from odoo.addons.pms_website_sale.controllers.booking_controller import (
    BookingEngineParser,
)


class PMSRouteCase(HttpCase):
    def setUp(self):
        super().setUp()
        self.public_partner = self.env.ref("base.public_partner")
        self.online_channel = self.env.ref("pms_website_sale.online_channel")
        self.single = self.env.ref("pms.pms_room_type_single")
        self.double = self.env.ref("pms.pms_room_type_double")

    def test_rooms_route(self):
        url = "/rooms"
        response = self.url_open(url=url)
        self.assertEqual(response.status_code, 200)
        page = fromstring(response.content)
        availability_divs = page.xpath("//form[@name='room_type_availability']")

        default_property_id = self.env["pms.booking.engine"]._default_pms_property_id()
        nb_room_types = len(
            self.env["pms.room.type"].get_room_types_by_property(default_property_id)
        )
        self.assertEqual(len(availability_divs), nb_room_types)

    def test_booking_route(self):
        url = "/booking"
        response = self.url_open(url=url)
        self.assertEqual(response.status_code, 200)
        page = fromstring(response.content)
        booking_page_div = page.xpath("//div[@name='booking_page']")
        self.assertTrue(booking_page_div)

    def test_booking_address_route(self):
        url = "/booking/address"
        response = self.url_open(url=url)
        self.assertEqual(response.status_code, 200)
        page = fromstring(response.content)
        booking_address_page_div = page.xpath("//div[@name='booking_address_page']")
        self.assertTrue(booking_address_page_div)
