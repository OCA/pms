from datetime import timedelta

from lxml.html import fromstring

from odoo.fields import Date
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

    def test_parse_empty_booking(self):
        today = Date.today()
        session = {
            BookingEngineParser.SESSION_KEY: {
                "partner_id": None,
                "start_date": Date.to_string(today),
                "end_date": Date.to_string(today + timedelta(days=3)),
                "rooms_requests": [],
            },
        }
        parser = BookingEngineParser(self.env, session)

        booking_engine = parser.parse()
        self.assertEqual(booking_engine.partner_id, self.public_partner)
        self.assertEqual(booking_engine.channel_type_id, self.online_channel)
        self.assertEqual(booking_engine.start_date, today)
        self.assertEqual(booking_engine.end_date, today + timedelta(days=3))
        self.assertTrue(
            all(
                ar.value_num_rooms_selected == 0
                for ar in booking_engine.availability_results
            )
        )

    def test_parse_booking_for_2_rooms(self):
        today = Date.today()
        session = {
            BookingEngineParser.SESSION_KEY: {
                "partner_id": None,
                "start_date": Date.to_string(today),
                "end_date": Date.to_string(today + timedelta(days=3)),
                "rooms_requests": [
                    {
                        "room_type_id": self.single.id,
                        "quantity": 1,
                    },
                    {
                        "room_type_id": self.double.id,
                        "quantity": 2,
                    },
                ],
            },
        }
        parser = BookingEngineParser(self.env, session)

        booking_engine = parser.parse()
        bookings = booking_engine.availability_results
        single_booking = bookings.filtered(
            lambda ar: ar.room_type_id.id == self.single.id
        )
        double_booking = bookings.filtered(
            lambda ar: ar.room_type_id.id == self.double.id
        )
        other_booking = bookings.filtered(
            lambda ar: ar.room_type_id.id not in (self.single.id, self.double.id)
        )
        self.assertEqual(single_booking.value_num_rooms_selected, 1)
        self.assertEqual(double_booking.value_num_rooms_selected, 2)
        self.assertTrue(
            all(booking.value_num_rooms_selected == 0 for booking in other_booking)
        )

    def test_booking_for_non_existent_room_raises_value_error(self):
        today = Date.today()
        session = {
            BookingEngineParser.SESSION_KEY: {
                "partner_id": None,
                "start_date": Date.to_string(today),
                "end_date": Date.to_string(today + timedelta(days=3)),
                "rooms_requests": [
                    {
                        "room_type_id": -1,
                        "quantity": 1,
                    },
                ],
            },
        }
        parser = BookingEngineParser(self.env, session)

        with self.assertRaises(ValueError) as e:
            parser.parse()
        self.assertTrue(str(e.exception).startswith("No room type"))

    def test_book_too_many_rooms_raises_value_error(self):
        today = Date.today()
        session = {
            BookingEngineParser.SESSION_KEY: {
                "partner_id": None,
                "start_date": Date.to_string(today),
                "end_date": Date.to_string(today + timedelta(days=3)),
                "rooms_requests": [
                    {
                        "room_type_id": self.single.id,
                        "quantity": 1000,
                    },
                ],
            },
        }
        parser = BookingEngineParser(self.env, session)

        with self.assertRaises(ValueError) as e:
            parser.parse()
        self.assertTrue(str(e.exception).startswith("Not enough rooms available"))
