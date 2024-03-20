# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Date

from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.pms_website_sale.controllers.booking_controller import (
    BookingEngineController,
)
from odoo.addons.pms_website_sale.controllers.booking_engine_parser import (
    AvailabilityErrorGroup,
    BookingEngineParser,
)
from odoo.addons.website.tools import MockRequest

from .pms_test_commons import PMSTestCommons


class BookingEngineControllerCase(PMSTestCommons):
    @classmethod
    def setUpClass(cls):
        super(BookingEngineControllerCase, cls).setUpClass()
        cls.controller = BookingEngineController()
        cls.public_user = cls.env.ref("base.public_user")
        cls.website = cls.env["website"].browse(1)

    def _get_date(self):
        return Date.from_string("2200-05-01")

    def _get_session_booking_engine(self):
        start_date = self._get_date()
        return {
            "partner_id": self.demo_partner.id,
            "partner": {
                "name": "Test Name",
                "email": "test@test.rt",
                "phone": "+322424242",
                "address": "Quai aux pierres, 3",
                "city": "Bruxelles",
                "postal_code": "1000",
                "country_id": self.env.company.country_id.id,
                "accepted_terms_and_conditions": True,
            },
            "start_date": Date.to_string(start_date),
            "end_date": Date.to_string(start_date + timedelta(days=3)),
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
        }

    def _create_folio(self):
        start_date = Date.from_string("2200-05-01")
        be = self.env["pms.booking.engine"].create(
            {
                "partner_id": self.demo_partner.id,
                "channel_type_id": self.online_channel.id,
                "start_date": start_date,
                "end_date": start_date + timedelta(days=3),
            }
        )
        availability_1 = be.availability_results.filtered(
            lambda ar: ar.room_type_id == self.room_type_1
        )
        availability_1.value_num_rooms_selected = 1
        availability_2 = be.availability_results.filtered(
            lambda ar: ar.room_type_id == self.room_type_2
        )
        availability_2.value_num_rooms_selected = 2
        folio_action = be.create_folio()
        return self.env["pms.folio"].browse(folio_action["res_id"])

    @staticmethod
    def _get_room_request_for_room_type(room_type_id: int, session):
        rooms_requests = session["rooms_requests"]
        room_request = [
            rr for rr in rooms_requests if rr["room_type_id"] == room_type_id
        ]
        return room_request.pop()

    def test_get_booking(self):
        with MockRequest(self.company.with_user(self.public_user).env) as request:
            request.session[
                BookingEngineParser.SESSION_KEY
            ] = self._get_session_booking_engine()
            booking_engine = self.controller._get_booking()
        self.assertEqual(booking_engine.partner_id, self.demo_partner)

    def test_post_booking(self):
        start_date = self._get_date()
        end_date = self._get_date() + timedelta(days=2)
        post = {
            "start_date": start_date,
            "end_date": end_date,
            "room_type_id": self.room_type_1.id,
            "quantity": 2,
        }
        be_session = self._get_session_booking_engine()
        with MockRequest(self.company.with_user(self.public_user).env) as request:
            request.session[BookingEngineParser.SESSION_KEY] = be_session
            booking_engine = self.controller._post_booking(**post)

        # no override of dates in post
        self.assertEqual(booking_engine.start_date, start_date)
        self.assertEqual(
            booking_engine.end_date, Date.from_string(be_session["end_date"])
        )

        be_ar_1 = booking_engine.availability_results.filtered(
            lambda ar: ar.room_type_id.id == self.room_type_1.id
        )
        self.assertEqual(be_ar_1.value_num_rooms_selected, 2)

    def test_delete_booking(self):
        # todo
        pass

    def test_get_booking_extra_info(self):
        # todo
        pass

    def test_post_booking_extra_info(self):
        # todo
        pass

    def test_get_booking_address(self):
        # todo
        pass

    def test_post_booking_address(self):
        # todo
        pass

    def test_booking_payment(self):
        with MockRequest(self.company.with_user(self.public_user).env) as request:
            request.session[
                BookingEngineParser.SESSION_KEY
            ] = self._get_session_booking_engine()
            values = self.controller._get_booking_payment()
        booking_engine = values["booking_engine"]
        self.assertEqual(booking_engine.partner_id.id, self.demo_partner.id)

    def test_booking_payment_transaction(self):
        with MockRequest(self.company.with_user(self.public_user).env) as request:
            request.session[
                BookingEngineParser.SESSION_KEY
            ] = self._get_session_booking_engine()
            tx = self.controller._post_booking_payment_transaction(
                self.wire_transfer_acquirer.id
            )

        untaxed_amount = (
            self.room_type_1.list_price + self.room_type_2.list_price * 2
        ) * 3
        expected_amount = 1.15 * untaxed_amount
        folio = tx.folio_ids
        self.assertEqual(tx.partner_id.name, "Test Name")
        self.assertEqual(tx.amount, expected_amount)
        self.assertEqual(
            tx.return_url, f"/ebooking/booking/success/{folio.id}/{folio.access_token}"
        )
        self.assertIn(tx.id, request.session["__payment_tx_ids__"])

    def test_booking_payment_transaction_fails_wo_terms_and_conditions(self):
        session = self._get_session_booking_engine()
        del session["partner"]["accepted_terms_and_conditions"]
        with MockRequest(self.company.with_user(self.public_user).env) as request:
            request.session[BookingEngineParser.SESSION_KEY] = session
            with self.assertRaises(ValidationError):
                self.controller._post_booking_payment_transaction(
                    self.wire_transfer_acquirer.id
                )

    def test_cancelling_transaction_cancels_folio(self):
        with MockRequest(self.company.with_user(self.public_user).env) as request:
            request.session[
                BookingEngineParser.SESSION_KEY
            ] = self._get_session_booking_engine()
            tx = self.controller._post_booking_payment_transaction(
                self.wire_transfer_acquirer.id
            )
        tx._set_transaction_cancel()
        folio = tx.folio_ids
        self.assertEqual(folio.state, "cancel")

    def test_get_booking_success(self):
        with MockRequest(
            self.company.with_user(self.public_user).env,
            website=self.website.with_user(self.public_user),
        ) as request:
            request.session[
                BookingEngineParser.SESSION_KEY
            ] = self._get_session_booking_engine()
            tx = self.controller._post_booking_payment_transaction(
                self.wire_transfer_acquirer.id
            )
            request.session[
                BookingEngineParser.SESSION_KEY
            ] = self._get_session_booking_engine()
            folio = tx.folio_ids
            tx.state = "done"
            tx.date = Date.today()
            PaymentProcessing().payment_status_poll()
            self.controller._get_booking_success(folio.id, folio.access_token)

        self.assertEqual(folio.state, "confirm")
        self.assertEqual(folio.move_ids.state, "posted")
        self.assertEqual(folio.move_ids.payment_state, "paid")
        self.assertFalse(request.session[BookingEngineParser.SESSION_KEY])

    def test_get_booking_success_raises_access_error(self):
        with MockRequest(
            self.company.with_user(self.public_user).env,
            website=self.website.with_user(self.public_user),
        ):
            folio = self._create_folio()
            with self.assertRaises(AccessError):
                self.controller._get_booking_success(folio.id, "forged-token")

    def test_booking_reset(self):
        # todo
        pass

    def test_booking_unavailable_rooms(self):
        session = self._get_session_booking_engine()
        session["rooms_requests"][0]["quantity"] = 1000
        with MockRequest(self.company.with_user(self.public_user).env) as request:
            request.session[BookingEngineParser.SESSION_KEY] = session

            with self.assertRaises(AvailabilityErrorGroup) as e:
                self.controller._get_booking_payment()
            self.assertIn("Some rooms are not available", str(e.exception))

    def test_booking_extra_info_unavailable_rooms(self):
        # todo
        pass

    def test_booking_address_unavailable_rooms(self):
        # todo
        pass

    def test_booking_payment_unavailable_rooms(self):
        session = self._get_session_booking_engine()
        session["rooms_requests"][0]["quantity"] = 1000
        with MockRequest(self.company.with_user(self.public_user).env) as request:
            request.session[BookingEngineParser.SESSION_KEY] = session

            with self.assertRaises(AvailabilityErrorGroup) as e:
                self.controller._post_booking_payment_transaction(
                    self.wire_transfer_acquirer.id
                )
            self.assertIn("Some rooms are not available", str(e.exception))

    def test_booking_payment_transaction_unavailable_rooms(self):
        session = self._get_session_booking_engine()
        session["rooms_requests"][0]["quantity"] = 1000
        with MockRequest(self.company.with_user(self.public_user).env) as request:
            request.session[BookingEngineParser.SESSION_KEY] = session
            with self.assertRaises(AvailabilityErrorGroup) as e:
                self.controller._get_booking_payment()
            self.assertIn("Some rooms are not available", str(e.exception))
