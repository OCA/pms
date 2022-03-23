import datetime

from odoo import fields
from odoo.exceptions import ValidationError

from .common import TestPms


class TestProductTemplate(TestPms):
    def setUp(self):
        super().setUp()
        self.room_type = self.env["pms.room.type"].create(
            {
                "name": "Room type test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        self.room = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Room test",
                "room_type_id": self.room_type.id,
                "capacity": 2,
            }
        )
        self.partner = self.env["res.partner"].create({"name": "partner1"})
        self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Board service test",
                "default_code": "BST",
            }
        )
        # create a sale channel
        self.sale_channel_direct1 = self.env["pms.sale.channel"].create(
            {
                "name": "Door",
                "channel_type": "direct",
            }
        )

    def test_bs_consumed_on_after(self):
        """
        Create a one day reservation with a board service configured to
        consume after reservation night.
        Date of service line with consumed on 'after' should match checkout date.
        """
        # ARRANGE
        product = self.env["product.product"].create(
            {
                "name": "Product test",
                "per_day": True,
                "consumed_on": "after",
            }
        )
        self.env["pms.board.service.line"].create(
            {
                "product_id": product.id,
                "pms_board_service_id": self.board_service.id,
            }
        )
        board_service_room_type = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type.id,
                "pms_board_service_id": self.board_service.id,
            }
        )
        date_checkin = fields.date.today()
        date_checkout = fields.date.today() + datetime.timedelta(days=1)
        # ACT
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": date_checkin,
                "checkout": date_checkout,
                "room_type_id": self.room_type.id,
                "pms_property_id": self.pms_property1.id,
                "partner_id": self.partner.id,
                "board_service_room_id": board_service_room_type.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        # ASSERT
        self.assertEqual(
            reservation.service_ids.service_line_ids.date,
            date_checkout,
            "Date of service line with consumed on 'after' should match checkout date.",
        )

    def test_bs_consumed_on_before(self):
        """
        Create a one day reservation with a board service configured to
        consume before reservation night.
        Date of service line with consumed on 'before' should match checkin date.
        """
        # ARRANGE
        product = self.env["product.product"].create(
            {
                "name": "Product test",
                "per_day": True,
                "consumed_on": "before",
            }
        )
        self.env["pms.board.service.line"].create(
            {
                "product_id": product.id,
                "pms_board_service_id": self.board_service.id,
            }
        )
        board_service_room_type = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type.id,
                "pms_board_service_id": self.board_service.id,
            }
        )
        date_checkin = fields.date.today()
        date_checkout = fields.date.today() + datetime.timedelta(days=1)
        # ACT
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": date_checkin,
                "checkout": date_checkout,
                "room_type_id": self.room_type.id,
                "pms_property_id": self.pms_property1.id,
                "partner_id": self.partner.id,
                "board_service_room_id": board_service_room_type.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        # ASSERT
        self.assertEqual(
            reservation.service_ids.service_line_ids.date,
            date_checkin,
            "Date of service line with consumed on 'before' should match checkin date.",
        )

    def test_bs_daily_limit_equal(self):
        """
        Create a one day reservation with a board service configured with
        daily limit = 2 and capacity = 2
        Reservation should created succesfully.
        """
        # ARRANGE
        product = self.env["product.product"].create(
            {
                "name": "Product test",
                "per_day": True,
                "daily_limit": 2,
                "per_person": True,
            }
        )
        self.env["pms.board.service.line"].create(
            {
                "product_id": product.id,
                "pms_board_service_id": self.board_service.id,
            }
        )
        board_service_room_type = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type.id,
                "pms_board_service_id": self.board_service.id,
            }
        )
        date_checkin = fields.date.today()
        date_checkout = fields.date.today() + datetime.timedelta(days=1)
        # ACT
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": date_checkin,
                "checkout": date_checkout,
                "room_type_id": self.room_type.id,
                "pms_property_id": self.pms_property1.id,
                "partner_id": self.partner.id,
                "board_service_room_id": board_service_room_type.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        reservation.flush()
        # ASSERT
        self.assertEqual(
            reservation.service_ids.service_line_ids.day_qty,
            self.room.capacity,
            "The reservation should have been created.",
        )

    def test_bs_daily_limit_lower(self):
        """
        Create a one day reservation with a board service configured with
        daily limit = 2 and capacity = 1
        Reservation should created succesfully.
        """
        # ARRANGE
        self.room.capacity = 1
        product = self.env["product.product"].create(
            {
                "name": "Product test",
                "per_day": True,
                "daily_limit": 2,
                "per_person": True,
            }
        )
        self.env["pms.board.service.line"].create(
            {
                "product_id": product.id,
                "pms_board_service_id": self.board_service.id,
            }
        )
        board_service_room_type = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type.id,
                "pms_board_service_id": self.board_service.id,
            }
        )
        date_checkin = fields.date.today()
        date_checkout = fields.date.today() + datetime.timedelta(days=1)
        # ACT
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": date_checkin,
                "checkout": date_checkout,
                "room_type_id": self.room_type.id,
                "pms_property_id": self.pms_property1.id,
                "partner_id": self.partner.id,
                "board_service_room_id": board_service_room_type.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        reservation.flush()
        # ASSERT
        # self.assertTrue(reservation, "The reservation should have been created.")
        # ASSERT
        self.assertEqual(
            reservation.service_ids.service_line_ids.day_qty,
            self.room.capacity,
            "The reservation should have been created.",
        )

    def test_bs_daily_limit_greater(self):
        """
        Create a one day reservation with a board service configured with
        daily limit = 1 and capacity = 2
        Reservation creation should fail.
        """
        # ARRANGE
        product = self.env["product.product"].create(
            {
                "name": "Product test",
                "per_day": True,
                "type": "service",
                "daily_limit": 1,
                "list_price": 15.0,
                "per_person": True,
            }
        )
        self.env["pms.board.service.line"].create(
            {
                "product_id": product.id,
                "pms_board_service_id": self.board_service.id,
            }
        )
        board_service_room_type = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type.id,
                "pms_board_service_id": self.board_service.id,
            }
        )
        date_checkin = fields.date.today()
        date_checkout = fields.date.today() + datetime.timedelta(days=1)
        # ACT & ASSERT
        with self.assertRaises(
            ValidationError, msg="Reservation created but it shouldn't"
        ):
            self.env["pms.reservation"].create(
                {
                    "checkin": date_checkin,
                    "checkout": date_checkout,
                    "room_type_id": self.room_type.id,
                    "pms_property_id": self.pms_property1.id,
                    "partner_id": self.partner.id,
                    "board_service_room_id": board_service_room_type.id,
                    "adults": 2,
                    "sale_channel_origin_id": self.sale_channel_direct1.id,
                }
            )

    # TODO: Review this test
    def _test_bs_is_extra_bed(self):
        # ARRANGE
        product = self.env["product.product"].create(
            {
                "name": "Product test",
                "per_day": True,
                "consumed_on": "after",
                "is_extra_bed": True,
            }
        )
        self.room.capacity = 1
        extra_bed_service = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": product.id,
            }
        )
        self.room.extra_beds_allowed = 1
        # ACT
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "room_type_id": self.room_type.id,
                "pms_property_id": self.pms_property1.id,
                "partner_id": self.partner.id,
                "service_ids": [extra_bed_service.id],
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        reservation._check_adults()
        reservation.flush()

    # TODO: pending tests (need review) -> per_day, per_person (with board service?)
