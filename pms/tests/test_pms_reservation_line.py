import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import TestPms


@tagged("post_install", "-at_install")
class TestPmsReservationLines(TestPms):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = cls.env["res.users"].browse(1)
        cls.env = cls.env(user=user)
        # create a room type availability
        cls.room_type_availability = cls.env["pms.availability.plan"].create(
            {
                "name": "Availability plan for TEST",
                "pms_pricelist_ids": [(6, 0, [cls.pricelist1.id])],
            }
        )

        # create room type
        cls.room_type_double = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": cls.room_type_class1.id,
            }
        )

        cls.room_type_triple = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id],
                "name": "Triple Test",
                "default_code": "TRP_Test",
                "class_id": cls.room_type_class1.id,
            }
        )

        # Additional room type class for incompatible test
        cls.room_type_class_day = cls.env["pms.room.type.class"].create(
            {
                "name": "Day Use",
                "overnight": False,
                "default_code": "DAY",
            }
        )
        cls.room_type_class_overnight = cls.env["pms.room.type.class"].create(
            {
                "name": "Overnight",
                "overnight": True,
                "default_code": "OVN",
            }
        )

        cls.room_type_day = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id],
                "name": "Day Room",
                "default_code": "DAY_Test",
                "class_id": cls.room_type_class_day.id,
            }
        )

        cls.room_type_overnight = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id],
                "name": "Overnight Room",
                "default_code": "OVN_Test",
                "class_id": cls.room_type_class_overnight.id,
            }
        )

        cls.room_day = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Day 201",
                "room_type_id": cls.room_type_day.id,
                "capacity": 1,
                "extra_beds_allowed": 0,
            }
        )
        cls.room_overnight = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Overnight 202",
                "room_type_id": cls.room_type_overnight.id,
                "capacity": 1,
                "extra_beds_allowed": 0,
            }
        )

        # create rooms
        cls.room1 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Double 101",
                "room_type_id": cls.room_type_double.id,
                "capacity": 2,
                "extra_beds_allowed": 1,
            }
        )

        cls.room2 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Double 102",
                "room_type_id": cls.room_type_double.id,
                "capacity": 2,
                "extra_beds_allowed": 1,
            }
        )

        cls.room3 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Double 103",
                "room_type_id": cls.room_type_double.id,
                "capacity": 2,
                "extra_beds_allowed": 1,
            }
        )

        cls.room4 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Triple 104",
                "room_type_id": cls.room_type_triple.id,
                "capacity": 3,
                "extra_beds_allowed": 1,
            }
        )
        cls.partner1 = cls.env["res.partner"].create(
            {
                "firstname": "Jaime",
                "lastname": "García",
                "email": "jaime@example.com",
                "birthdate_date": "1983-03-01",
                "gender": "male",
            }
        )
        cls.sale_channel_direct = cls.env["pms.sale.channel"].create(
            {"name": "sale channel direct", "channel_type": "direct"}
        )
        cls.sale_channel1 = cls.env["pms.sale.channel"].create(
            {"name": "saleChannel1", "channel_type": "indirect"}
        )
        cls.agency1 = cls.env["res.partner"].create(
            {
                "firstname": "partner1",
                "is_agency": True,
                "invoice_to_agency": "always",
                "default_commission": 15,
                "sale_channel_id": cls.sale_channel1.id,
            }
        )

    @freeze_time("2000-12-01")
    def test_modify_reservation_line_with_compatible_overnight_classes(self):
        """
        Check that when modifying a reservation with compatible overnight
        classes, the reservation is modified correctly.
        """
        # ARRANGE
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=3)
        reservation_vals = {
            "checkin": checkin,
            "checkout": checkout,
            "room_type_id": self.room_type_double.id,
            "partner_id": self.partner1.id,
            "pms_property_id": self.pms_property1.id,
            "sale_channel_origin_id": self.sale_channel_direct.id,
        }
        reservation = self.env["pms.reservation"].create(reservation_vals)

        # ACT
        reservation.reservation_line_ids[0].write(
            {
                "room_id": self.room_overnight.id,
            }
        )

        # ASSERT
        self.assertEqual(
            reservation.reservation_line_ids[0].room_id.room_type_id.id,
            self.room_type_overnight.id,
            "The reservation should be modified with the new room type",
        )

    @freeze_time("2000-12-01")
    def test_auto_assignment_follows_assignment_sequence(self):
        """
        Check that the automatic room assignment of a reservation without
        room preassigned follows the assignment_sequence order of the rooms
        instead of the display order (sequence).
        """
        # ARRANGE
        # Display order: room1 < room2 < room3
        # Assignment order: room3 < room2 < room1
        self.room1.write({"sequence": 1, "assignment_sequence": 3})
        self.room2.write({"sequence": 2, "assignment_sequence": 2})
        self.room3.write({"sequence": 3, "assignment_sequence": 1})
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=3)

        # ACT
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": checkin,
                "checkout": checkout,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct.id,
            }
        )

        # ASSERT
        self.assertEqual(
            reservation.reservation_line_ids.room_id,
            self.room3,
            "The room with the lowest assignment_sequence should be "
            "assigned first on reservations without room preassigned",
        )

    def test_room_assignment_sequence_defaults_to_sequence(self):
        """
        Check that the assignment_sequence of a new room takes the same
        value as the sequence when it is not explicitly set.
        """
        # ACT
        room = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Double 105",
                "room_type_id": self.room_type_double.id,
                "capacity": 2,
                "sequence": 7,
            }
        )

        # ASSERT
        self.assertEqual(
            room.assignment_sequence,
            7,
            "The assignment_sequence of a new room should default " "to its sequence",
        )

    @freeze_time("2000-12-01")
    def test_modify_reservation_with_incompatible_overnight_classes(self):
        """
        Check that when modifying a reservation with incompatible overnight
        classes, the reservation raises an error.
        """
        # ARRANGE
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=3)
        reservation_vals = {
            "checkin": checkin,
            "checkout": checkout,
            "room_type_id": self.room_type_double.id,
            "partner_id": self.partner1.id,
            "pms_property_id": self.pms_property1.id,
            "sale_channel_origin_id": self.sale_channel_direct.id,
        }
        reservation = self.env["pms.reservation"].create(reservation_vals)

        # ACT & ASSERT
        with self.assertRaises(ValidationError):
            reservation.reservation_line_ids[0].write(
                {
                    "room_id": self.room_day.id,
                }
            )

    @freeze_time("2000-12-01")
    def test_no_archived_room_in_split_assignment(self):
        """
        Room auto-assignment must never pick archived rooms, even when
        the environment context carries active_test=False (e.g. records
        created from connector imports, where the binder returns records
        with that context).

        No active double room is free for the whole stay, so the
        assignment falls back to the night-by-night ranking. An archived
        room, having no reservation lines, always ranks best and would
        win the ranking if not filtered out, leaving the reservation
        assigned to a room that is invisible in the planning and does
        not consume availability.
        """
        # ARRANGE
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=2)
        # room1 is taken the first night, room2 the second night,
        # so no active double room is free for the entire stay
        self.env["pms.reservation"].create(
            {
                "checkin": checkin,
                "checkout": checkin + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct.id,
            }
        )
        self.env["pms.reservation"].create(
            {
                "checkin": checkin + datetime.timedelta(days=1),
                "checkout": checkout,
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct.id,
            }
        )
        self.room3.active = False

        # ACT
        reservation = (
            self.env["pms.reservation"]
            .with_context(active_test=False)
            .create(
                {
                    "checkin": checkin,
                    "checkout": checkout,
                    "room_type_id": self.room_type_double.id,
                    "partner_id": self.partner1.id,
                    "pms_property_id": self.pms_property1.id,
                    "sale_channel_origin_id": self.sale_channel_direct.id,
                }
            )
        )

        # ASSERT
        self.assertNotIn(
            self.room3,
            reservation.reservation_line_ids.room_id,
            "Archived rooms must not be auto-assigned to reservations",
        )
        self.assertTrue(
            all(reservation.reservation_line_ids.room_id.mapped("active")),
            "All rooms auto-assigned to a reservation must be active",
        )
