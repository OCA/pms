# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo.fields import Date

from odoo.addons.pms_website_sale.controllers.booking_engine_parser import (
    BookingEngineParser,
    ParserError,
)

from .pms_test_commons import PMSTestCommons


class BookingParserCase(PMSTestCommons):
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
                        "room_type_id": self.room_type_1.id,
                        "quantity": 1,
                    },
                    {
                        "room_type_id": self.room_type_2.id,
                        "quantity": 2,
                    },
                ],
            },
        }
        parser = BookingEngineParser(self.env, session)

        booking_engine = parser.parse()
        bookings = booking_engine.availability_results
        room_type_1_booking = bookings.filtered(
            lambda ar: ar.room_type_id.id == self.room_type_1.id
        )
        room_type_2_booking = bookings.filtered(
            lambda ar: ar.room_type_id.id == self.room_type_2.id
        )
        other_booking = bookings.filtered(
            lambda ar: ar.room_type_id.id
            not in (self.room_type_1.id, self.room_type_2.id)
        )
        self.assertEqual(room_type_1_booking.value_num_rooms_selected, 1)
        self.assertEqual(room_type_2_booking.value_num_rooms_selected, 2)
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

        with self.assertRaises(ParserError) as e:
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
                        "room_type_id": self.room_type_1.id,
                        "quantity": 1000,
                    },
                ],
            },
        }
        parser = BookingEngineParser(self.env, session)

        with self.assertRaises(ParserError) as e:
            parser.parse()
        self.assertTrue(str(e.exception).startswith("Not enough rooms available"))

    def test_parse_booking_with_partner(self):
        today = Date.today()
        session = {
            BookingEngineParser.SESSION_KEY: {
                "partner_id": self.demo_partner.id,
                "start_date": Date.to_string(today),
                "end_date": Date.to_string(today + timedelta(days=3)),
                "rooms_request": [
                    {
                        "room_type_id": self.room_type_1.id,
                        "room_name": self.room_type_1.name,
                        "quantity": 1,
                    },
                    {
                        "room_type_id": self.room_type_2.id,
                        "room_name": self.room_type_2.name,
                        "quantity": 2,
                    },
                ],
            }
        }
        parser = BookingEngineParser(self.env, session)

        booking_engine = parser.parse()
        self.assertEqual(booking_engine.partner_id, self.demo_partner)
