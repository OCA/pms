# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

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
        url = "/ebooking/rooms"
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
        url = "/ebooking/rooms?start_date=2023-12-01&end_date=2023-01-01"
        response = self.url_open(url=url)
        self.assertEqual(response.status_code, 200)
        page = fromstring(response.content)
        error_div = page.xpath("//div[@name='errors']")
        self.assertTrue(error_div)

    def test_booking_route(self):
        url = "/ebooking/booking"
        response = self.url_open(url=url)
        self.assertEqual(response.status_code, 200)
        page = fromstring(response.content)
        booking_page_div = page.xpath("//div[@name='booking_page']")
        self.assertTrue(booking_page_div)

    @mock.patch("odoo.http.WebRequest.validate_csrf", return_value=True)
    def test_booking_route_with_delete_errors(self, _):
        url = "/ebooking/booking"

        data = {"delete": "-1"}  # deleting non existing room request
        response = self.url_open(url=url, data=data)
        self.assertEqual(response.status_code, 200)
        page = fromstring(response.content)
        error_div = page.xpath("//div[@name='errors']")
        self.assertTrue(error_div)

        data = {"delete": "a"}  # deleting with wrong value
        response = self.url_open(url=url, data=data)
        self.assertEqual(response.status_code, 200)
        page = fromstring(response.content)
        error_div = page.xpath("//div[@name='errors']")
        self.assertTrue(error_div)

    @mock.patch("odoo.http.WebRequest.validate_csrf", return_value=True)
    def test_booking_route_with_room_request(self, _):
        url = "/ebooking/booking"
        room_type_class_1 = self.env["pms.room.type.class"].create(
            {
                "name": "room type class 1",
                "default_code": "RTC1",
            }
        )
        room_type_1 = self.env["pms.room.type"].create(
            {
                "name": "room type 1",
                "default_code": "RT1",
                "class_id": room_type_class_1.id,
            }
        )
        data = {
            "room_type_id": room_type_1.id,
            "quantity": 1,
            "start_date": "",
            "end_date": "",
        }
        response = self.url_open(url=url, data=data)
        self.assertEqual(response.status_code, 200)
        page = fromstring(response.content)
        booking_page_div = page.xpath("//div[@name='booking_page']")
        self.assertTrue(booking_page_div)

    @mock.patch("odoo.http.WebRequest.validate_csrf", return_value=True)
    def test_booking_route_with_room_request_errors(self, _):
        url = "/ebooking/booking"
        data = {
            "room_type_id": -1,
            "quantity": -1,
            "start_date": "",
            "end_date": "",
        }
        response = self.url_open(url=url, data=data)
        self.assertEqual(response.status_code, 200)
        page = fromstring(response.content)
        error_div = page.xpath("//div[@name='errors']")
        self.assertTrue(error_div)

    def test_booking_address_route(self):
        url = "/ebooking/booking/address"
        response = self.url_open(url=url)
        self.assertEqual(response.status_code, 200)
        page = fromstring(response.content)
        booking_address_page_div = page.xpath("//div[@name='booking_address_page']")
        self.assertTrue(booking_address_page_div)

    def test_booking_payment_route(self):
        url = "/ebooking/booking/payment"
        response = self.url_open(url=url)
        self.assertEqual(response.status_code, 200)
        page = fromstring(response.content)
        booking_payment_div = page.xpath("//div[@name='booking_payment_page']")
        self.assertTrue(booking_payment_div)

    def test_booking_payment_success_route_notfound(self):
        url = "/ebooking/booking/success/0"
        response = self.url_open(url=url)
        self.assertEqual(response.status_code, 404)
