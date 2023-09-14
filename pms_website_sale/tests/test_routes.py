# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import json
from unittest import mock

from lxml.html import fromstring

import odoo
from odoo.tests.common import HttpCase


@odoo.tests.tagged("post_install", "-at_install")
class PMSRouteCase(HttpCase):
    def setUp(self):
        super().setUp()
        self.public_user = self.env.ref("base.public_user")
        self.acquirer = self.env.ref("payment.payment_acquirer_transfer")
        self.website = self.env["website"].browse(1)

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

    def test_rooms_route_with_errors(self):
        url = "/rooms?start_date=2023-12-01&end_date=2023-01-01"
        response = self.url_open(url=url)
        self.assertEqual(response.status_code, 200)
        page = fromstring(response.content)
        error_div = page.xpath("//div[@name='errors']")
        self.assertTrue(error_div)

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

    def test_booking_payment_route(self):
        url = "/booking/payment"
        response = self.url_open(url=url)
        self.assertEqual(response.status_code, 200)
        page = fromstring(response.content)
        booking_payment_div = page.xpath("//div[@name='booking_payment_page']")
        self.assertTrue(booking_payment_div)

    @mock.patch("odoo.http.WebRequest.validate_csrf", return_value=True)
    def test_booking_payment_transaction_route(self, redirect_mock):
        url = "/booking/payment/transaction"
        data = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "acquirer_id": self.acquirer.id,
                "success_url": "/booking/payment/success",
            },
        }
        response = self.url_open(
            url=url,
            headers={"content-type": "application/json"},
            data=json.dumps(data),
        )
        self.assertEqual(response.status_code, 200)

    # def test_booking_payment_success_route(self):
    #     folio = self.env.ref("pms.pms_folio_eco_01")
    #     url = f"/booking/success/{folio.id}"
    #     with MockRequest(
    #         folio.with_user(self.public_user).env,
    #         website=self.website.with_user(self.public_user),
    #     ):
    #         response = self.url_open(url=url)
    #     self.assertEqual(response.status_code, 200)
    #     page = fromstring(response.content)
    #     booking_payment_success_div = page.xpath("//div[@name='booking_success_page']")
    #     self.assertTrue(booking_payment_success_div)

    def test_booking_payment_success_route_notfound(self):
        url = "/booking/success/0"
        response = self.url_open(url=url)
        self.assertEqual(response.status_code, 404)

    def test_booking_payment_failure_route(self):
        url = "/booking/failure"
        response = self.url_open(url=url)
        self.assertEqual(response.status_code, 200)
        page = fromstring(response.content)
        booking_payment_failure_div = page.xpath("//div[@name='booking_failure_page']")
        self.assertTrue(booking_payment_failure_div)
