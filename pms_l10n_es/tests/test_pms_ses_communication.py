from odoo import fields
from odoo.tools.safe_eval import datetime

from .common import TestPms


class TestPmsSesCommunication(TestPms):
    def setUp(self):
        super().setUp()
        self.sale_channel_direct1 = self.env["pms.sale.channel"].create(
            {
                "name": "Door",
                "channel_type": "direct",
            }
        )
        # create room type
        self.room_type = self.env["pms.room.type"].create(
            {
                "name": "Room type test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        # room
        self.room_double_1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Room test 1",
                "room_type_id": self.room_type.id,
                "capacity": 2,
            }
        )
        self.pms_property1.institution = "ses"

    def test_create_notification_when_create_reservation(self):
        # ARRANGE/ACT
        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type.id,
                "checkin": "2021-01-01",
                "checkout": "2021-01-02",
                "adults": 2,
                "children": 0,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
                "partner_name": "Test reservation",
            }
        )
        # ASSERT
        last_notification = self.env["pms.ses.communication"].search(
            [
                ("reservation_id", "=", reservation.id),
            ]
        )
        self.assertEqual(
            last_notification.operation,
            "A",
            "Creating a reservation should create a notification with operation A",
        )

    def test_not_create_notification_when_cancel_reservation_and_not_sent(self):
        # ARRANGE
        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type.id,
                "checkin": fields.date.today() + datetime.timedelta(days=1),
                "checkout": fields.date.today() + datetime.timedelta(days=2),
                "adults": 2,
                "children": 0,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
                "partner_name": "Test reservation",
            }
        )
        # ACT
        reservation.action_cancel()
        # ASSERT
        last_notifications = self.env["pms.ses.communication"].search(
            [
                ("reservation_id", "=", reservation.id),
            ],
            order="id",
        )
        self.assertFalse(
            last_notifications,
            "Cancelling a reservation not sent should not create a notification",
        )

    def test_create_notification_when_cancel_reservation_and_is_sent(self):
        # ARRANGE
        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type.id,
                "checkin": fields.date.today() + datetime.timedelta(days=1),
                "checkout": fields.date.today() + datetime.timedelta(days=2),
                "adults": 2,
                "children": 0,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
                "partner_name": "Test reservation",
            }
        )
        notification_after_create_reservation = self.env[
            "pms.ses.communication"
        ].search(
            [
                ("reservation_id", "=", reservation.id),
                ("operation", "=", "A"),
            ]
        )
        notification_after_create_reservation.state = "to_process"
        # ACT
        reservation.action_cancel()
        # ASSERT
        last_notifications = (
            self.env["pms.ses.communication"]
            .search(
                [
                    ("reservation_id", "=", reservation.id),
                ],
                order="id",
            )
            .mapped("operation")
        )
        self.assertEqual(
            last_notifications,
            ["A", "B"],
            "Canceling a reservation should create a notification with operation B",
        )

    def test_create_notification_when_modify_reservation_and_not_sent(self):
        # ARRANGE
        update_operations = [
            {
                "adults": 1,
            },
            {
                "checkin": fields.date.today() + datetime.timedelta(days=10),
            },
            {
                "checkout": fields.date.today() + datetime.timedelta(days=12),
            },
        ]
        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type.id,
                "checkin": fields.date.today() + datetime.timedelta(days=1),
                "checkout": fields.date.today() + datetime.timedelta(days=13),
                "adults": 2,
                "children": 0,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
                "partner_name": "Test reservation",
            }
        )
        # ACT & ASSERT
        for _index, update_operation in enumerate(update_operations):
            with self.subTest(k=update_operation):
                reservation.write(update_operation)
                last_notification_operations = (
                    self.env["pms.ses.communication"]
                    .search(
                        [
                            ("reservation_id", "=", reservation.id),
                        ],
                        order="id",
                    )
                    .mapped("operation")
                )
                self.assertEqual(
                    ["A"],
                    last_notification_operations,
                    "Update adults should create 2 notifications "
                    "with operations A and B",
                )

    def test_create_notification_when_modify_reservation_and_is_sent(self):
        # ARRANGE
        update_operations = [
            {
                "adults": 1,
            },
            {
                "checkin": fields.date.today() + datetime.timedelta(days=10),
            },
            {
                "checkout": fields.date.today() + datetime.timedelta(days=12),
            },
        ]
        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type.id,
                "checkin": fields.date.today() + datetime.timedelta(days=1),
                "checkout": fields.date.today() + datetime.timedelta(days=13),
                "adults": 2,
                "children": 0,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
                "partner_name": "Test reservation",
            }
        )
        reservation_communications = self.env["pms.ses.communication"].search(
            [("reservation_id", "=", reservation.id)]
        )
        reservation_communications.state = "to_process"
        # ACT & ASSERT
        for _index, update_operation in enumerate(update_operations):
            with self.subTest(k=update_operation):
                reservation.write(update_operation)
                reservation_communications = (
                    self.env["pms.ses.communication"]
                    .search(
                        [
                            ("reservation_id", "=", reservation.id),
                        ],
                        order="id",
                    )
                    .mapped("operation")
                )
                self.assertEqual(
                    ["A", "B", "A"],
                    reservation_communications,
                    "Update adults should create 2 "
                    "notifications with operations A and B",
                )
