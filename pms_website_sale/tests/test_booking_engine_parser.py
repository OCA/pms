# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo.fields import Date

from odoo.addons.pms_website_sale.controllers.booking_engine_parser import (
    AvailabilityErrorGroup,
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

        with self.assertRaises(AvailabilityErrorGroup) as e:
            parser.parse()
            self.assertIn("Some rooms are not available", str(e.exception))

    def test_set_internal_comment(self):
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

        internal_comment = "PMR access needed"

        parser.set_internal_comment(internal_comment)
        self.assertEqual(parser.data.get("internal_comment"), internal_comment)

    def test_set_partner(self):
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

        values = {
            "name": "Test",
            "email": "test@test.rt",
            "phone": "+322424242",
            "address": "Quai aux pierres, 3",
            "city": "Bruxelles",
            "postal_code": "1000",
            "country_id": self.env.company.country_id.id,
            "accepted_terms_and_conditions": "on",
        }

        parser.set_partner(**values)

        expected_values = values.copy()
        expected_values["accepted_terms_and_conditions"] = True
        self.assertEqual(parser.data["partner"], expected_values)

    def test_set_partner_missing_required_field(self):
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

        values = {
            "name": "",
            "email": "test@test.rt",
            "phone": "+322424242",
            "address": "Quai aux pierres, 3",
            "city": "Bruxelles",
            "postal_code": "1000",
            "country_id": self.env.company.country_id.id,
            "accepted_terms_and_conditions": "on",
        }

        with self.assertRaises(ParserError) as e:
            parser.set_partner(**values)
            self.assertTrue(str(e.exception).endswith("is required."))
        self.assertFalse(parser.data.get("partner"))

    def test_set_partner_email_error(self):
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

        values = {
            "name": "Test",
            "email": "this_is_a_wrong_email",
            "phone": "+322424242",
            "address": "Quai aux pierres, 3",
            "city": "Bruxelles",
            "postal_code": "1000",
            "country_id": self.env.company.country_id.id,
            "accepted_terms_and_conditions": "on",
        }

        with self.assertRaises(ParserError) as e:
            parser.set_partner(**values)
            self.assertEqual(str(e.exception), "Email address is not valid.")
        self.assertFalse(parser.data.get("partner"))

    def test_set_partner_country_error(self):
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

        values = {
            "name": "Test",
            "email": "this_is_a_wrong_email",
            "phone": "+322424242",
            "address": "Quai aux pierres, 3",
            "city": "Bruxelles",
            "postal_code": "1000",
            "country_id": "0",
            "accepted_terms_and_conditions": "on",
        }

        with self.assertRaises(ParserError) as e:
            parser.set_partner(**values)
            self.assertEqual(str(e.exception), "Wrong value for Country.")
        self.assertFalse(parser.data.get("partner"))

        values["country_id"] = "this is non digit value for country"

        with self.assertRaises(ParserError) as e:
            parser.set_partner(**values)
            self.assertEqual(str(e.exception), "Incorrect value for Country.")
        self.assertFalse(parser.data.get("partner"))

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

    def test_create_folio(self):
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
                ],
            },
        }
        parser = BookingEngineParser(self.env, session)

        values = {
            "name": "Test",
            "email": "test@test.rt",
            "phone": "+322424242",
            "address": "Quai aux pierres, 3",
            "city": "Bruxelles",
            "postal_code": "1000",
            "country_id": self.env.company.country_id.id,
            "accepted_terms_and_conditions": "on",
        }

        parser.set_partner(**values)
        parser.parse()
        folio = parser.create_folio()
        self.assertTrue(folio.partner_id)
        self.assertTrue(folio.email, "test@test.rt")
        self.assertTrue(folio.mobile, "+322424242")
