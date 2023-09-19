# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo.fields import Date

from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.pms_website_sale.controllers.booking_controller import (
    BookingEngineController,
)
from odoo.addons.pms_website_sale.controllers.booking_engine_parser import (
    AvailabilityError,
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

    def _get_session_booking_engine(self):
        start_date = Date.from_string("2200-05-01")
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

    def test_booking_payment(self):
        with MockRequest(self.company.with_user(self.public_user).env) as request:
            request.session[
                BookingEngineParser.SESSION_KEY
            ] = self._get_session_booking_engine()
            values = self.controller._booking_payment()
        booking_engine = values["booking_engine"]
        self.assertEqual(booking_engine.partner_id.id, self.demo_partner.id)

    def test_booking_payment_transaction(self):
        with MockRequest(self.company.with_user(self.public_user).env) as request:
            request.session[
                BookingEngineParser.SESSION_KEY
            ] = self._get_session_booking_engine()
            tx = self.controller._booking_payment_transaction(
                self.wire_transfer_acquirer.id
            )

        untaxed_amount = (
            self.room_type_1.list_price + self.room_type_2.list_price * 2
        ) * 3
        expected_amount = 1.15 * untaxed_amount
        folio = tx.folio_ids
        self.assertEqual(tx.partner_id.name, "Test Name")
        self.assertEqual(tx.amount, expected_amount)
        self.assertEqual(tx.return_url, f"/ebooking/booking/success/{folio.id}")
        self.assertIn(tx.id, request.session["__payment_tx_ids__"])

    def test_cancelling_transaction_cancels_folio(self):
        with MockRequest(self.company.with_user(self.public_user).env) as request:
            request.session[
                BookingEngineParser.SESSION_KEY
            ] = self._get_session_booking_engine()
            tx = self.controller._booking_payment_transaction(
                self.wire_transfer_acquirer.id
            )
        tx._set_transaction_cancel()
        folio = tx.folio_ids
        self.assertEqual(folio.state, "cancel")

    def test_booking_success(self):
        with MockRequest(
            self.company.with_user(self.public_user).env,
            website=self.website.with_user(self.public_user),
        ) as request:
            request.session[
                BookingEngineParser.SESSION_KEY
            ] = self._get_session_booking_engine()
            tx = self.controller._booking_payment_transaction(
                self.wire_transfer_acquirer.id
            )
            request.session[
                BookingEngineParser.SESSION_KEY
            ] = self._get_session_booking_engine()
            folio = tx.folio_ids
            tx.state = "done"
            tx.date = Date.today()
            PaymentProcessing().payment_status_poll()
            self.controller._booking_success(folio.id)

        self.assertEqual(folio.state, "confirm")
        self.assertEqual(folio.move_ids.state, "posted")
        self.assertEqual(folio.move_ids.payment_state, "paid")
        self.assertFalse(request.session[BookingEngineParser.SESSION_KEY])

    def test_booking_unavailable_rooms(self):
        # todo
        pass

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

            with self.assertRaises(AvailabilityError) as e:
                self.controller._booking_payment_transaction(
                    self.wire_transfer_acquirer.id
                )
            self.assertIn("Not enough rooms available for", str(e.exception))

    def test_booking_payment_transaction_unavailable_rooms(self):
        session = self._get_session_booking_engine()
        session["rooms_requests"][0]["quantity"] = 1000
        with MockRequest(self.company.with_user(self.public_user).env) as request:
            request.session[BookingEngineParser.SESSION_KEY] = session
            with self.assertRaises(AvailabilityError) as e:
                self.controller._booking_payment()
            self.assertIn("Not enough rooms available for", str(e.exception))
