# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo.fields import Date

from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.pms_website_sale.controllers.booking_controller import (
    BookingEngineController,
)
from odoo.addons.pms_website_sale.controllers.booking_engine_parser import (
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

        start_date = Date.from_string("2200-05-01")
        cls.session_booking_engine = {
            "partner_id": cls.demo_partner.id,
            "start_date": Date.to_string(start_date),
            "end_date": Date.to_string(start_date + timedelta(days=3)),
            "rooms_requests": [
                {
                    "room_type_id": cls.room_type_1.id,
                    "quantity": 1,
                },
                {
                    "room_type_id": cls.room_type_2.id,
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
            ] = self.session_booking_engine
            values = self.controller._booking_payment()
        booking_engine = values["booking_engine"]
        self.assertEqual(booking_engine.partner_id.id, self.demo_partner.id)

    def test_booking_payment_transaction(self):
        with MockRequest(self.company.with_user(self.public_user).env) as request:
            request.session[
                BookingEngineParser.SESSION_KEY
            ] = self.session_booking_engine
            tx = self.controller._booking_payment_transaction(
                self.wire_transfer_acquirer.id
            )

        untaxed_amount = (
            self.room_type_1.list_price + self.room_type_2.list_price * 2
        ) * 3
        expected_amount = 1.15 * untaxed_amount
        folio = tx.folio_ids
        self.assertEqual(tx.partner_id, self.demo_partner)
        self.assertEqual(tx.amount, expected_amount)
        self.assertEqual(tx.return_url, f"/booking/success/{folio.id}")
        self.assertIn(tx.id, request.session["__payment_tx_ids__"])

    def test_booking_success(self):
        with MockRequest(
            self.company.with_user(self.public_user).env,
            website=self.website.with_user(self.public_user),
        ) as request:
            request.session[
                BookingEngineParser.SESSION_KEY
            ] = self.session_booking_engine
            tx = self.controller._booking_payment_transaction(
                self.wire_transfer_acquirer.id
            )
            request.session[
                BookingEngineParser.SESSION_KEY
            ] = self.session_booking_engine
            folio = tx.folio_ids
            tx.state = "done"
            tx.date = Date.today()
            PaymentProcessing().payment_status_poll()
            self.controller._booking_success(folio.id)

        self.assertEqual(folio.state, "confirm")
        self.assertEqual(folio.move_ids.state, "posted")
        self.assertEqual(folio.move_ids.payment_state, "paid")
        self.assertFalse(request.session[BookingEngineParser.SESSION_KEY])
