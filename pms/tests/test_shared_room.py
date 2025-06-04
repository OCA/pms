import datetime

from odoo import fields
from odoo.exceptions import ValidationError

from .common import TestPms


class TestPmsSharedRoom(TestPms):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # create a room type availability
        cls.room_type_availability = cls.env["pms.availability.plan"].create(
            {
                "name": "Availability plan for TEST",
                "pms_pricelist_ids": [(6, 0, [cls.pricelist1.id])],
            }
        )

        cls.bed_class = cls.env["pms.room.type.class"].create(
            {
                "name": "Bed Class 1",
                "default_code": "B1",
            }
        )

        # create room type
        cls.room_type_test = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id],
                "name": "Shared Test",
                "default_code": "SHT",
                "class_id": cls.room_type_class1.id,
            }
        )

        cls.room_type_bed = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id],
                "name": "Bed Type Test",
                "default_code": "BTT",
                "class_id": cls.bed_class.id,
            }
        )

        # create shared room
        cls.room1 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Shared 101",
                "room_type_id": cls.room_type_test.id,
                "capacity": 2,
            }
        )

        # create beds in room1
        cls.r1bed1 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "101 (1)",
                "room_type_id": cls.room_type_bed.id,
                "capacity": 1,
                "parent_id": cls.room1.id,
            }
        )

        cls.r1bed2 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "101 (2)",
                "room_type_id": cls.room_type_bed.id,
                "capacity": 2,
                "parent_id": cls.room1.id,
            }
        )

        # create partner
        cls.partner1 = cls.env["res.partner"].create(
            {
                "firstname": "Jaime",
                "lastname": "García",
                "email": "jaime@example.com",
                "birthdate_date": "1983-03-01",
                "gender": "male",
            }
        )

        # create a sale channel
        cls.sale_channel_direct1 = cls.env["pms.sale.channel"].create(
            {
                "name": "Door",
                "channel_type": "direct",
            }
        )

    def test_count_avail_beds_with_room_occupied(self):
        """
        Check that not allow to create a bed reservation with a room occupied
        ----------------
        Create a room1 reservation and check that the beds room real avail is 0
        """

        # ARRANGE
        today = fields.date.today()
        tomorrow = fields.date.today() + datetime.timedelta(days=1)

        # ACT
        self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "preferred_room_id": self.room1.id,
                "checkin": today,
                "checkout": tomorrow,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ASSERT
        self.assertEqual(
            self.pms_property1.with_context(
                checkin=today,
                checkout=tomorrow,
                room_type_id=self.room_type_bed.id,
            ).availability,
            0,
            "Beds avaialbility should be 0 for room occupied",
        )

    def test_count_avail_shared_room_with_one_bed_occupied(self):
        """
        Check that not allow to create a shared room reservation with a bed occupied
        ----------------
        Create a room1's bed reservation and check that the room1 real avail is 0
        """

        # ARRANGE
        today = fields.date.today()
        tomorrow = fields.date.today() + datetime.timedelta(days=1)

        # ACT
        self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "preferred_room_id": self.r1bed1.id,
                "checkin": today,
                "checkout": tomorrow,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ASSERT
        self.assertEqual(
            self.pms_property1.with_context(
                checkin=today,
                checkout=tomorrow,
                room_type_id=self.room_type_test.id,
            ).availability,
            0,
            "Shared Room avaialbility should be 0 if it has a bed occupied",
        )

    def test_avail_in_room_type_with_shared_rooms(self):
        """
        Check that a shared room's bed occupied not
        affect the avail on other rooms with the
        same room type
        ----------------
        Create other room like room_type_test (room2)
        Create a room1's bed reservation and check that the room1
        Check that room_type_test real avail is 1
        """

        # ARRANGE
        today = fields.date.today()
        tomorrow = fields.date.today() + datetime.timedelta(days=1)
        self.room2 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Shared 102",
                "room_type_id": self.room_type_test.id,
                "capacity": 2,
            }
        )

        # ACT
        self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "preferred_room_id": self.r1bed1.id,
                "checkin": today,
                "checkout": tomorrow,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ASSERT
        self.assertEqual(
            self.pms_property1.with_context(
                checkin=today,
                checkout=tomorrow,
                room_type_id=self.room_type_test.id,
            ).availability,
            1,
            "Room not shared affect by the shared room's avail with the same type",
        )

    def test_count_avail_beds_with_one_bed_occupied(self):
        """
        Check the avail of a bed when it has
        a room with other beds occupied
        ----------------
        Create a room1's bed (it has 2 beds)
        reservation and check that the beds avail = 1
        """

        # ARRANGE
        today = fields.date.today()
        tomorrow = fields.date.today() + datetime.timedelta(days=1)

        # ACT
        res1 = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "preferred_room_id": self.r1bed1.id,
                "checkin": today,
                "checkout": tomorrow,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        res1.flush_recordset()
        # ASSERT
        self.assertEqual(
            self.pms_property1.with_context(
                checkin=today,
                checkout=tomorrow,
                room_type_id=self.room_type_bed.id,
            ).availability,
            1,
            "Beds avaialbility should be 1 if it has 1 of 2 beds occupied",
        )

    def test_not_avail_beds_with_room_occupied(self):
        """
        Check that not allow to select a bed with a room occupied
        ----------------
        Create a room1 reservation and check that the beds are not available
        """

        # ARRANGE
        today = fields.date.today()
        tomorrow = fields.date.today() + datetime.timedelta(days=1)

        # ACT
        self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "preferred_room_id": self.room1.id,
                "checkin": today,
                "checkout": tomorrow,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ASSERT
        self.assertNotIn(
            self.r1bed1.id,
            self.pms_property1.with_context(
                checkin=today,
                checkout=tomorrow,
                room_type_id=self.room_type_bed.id,
            ).free_room_ids.ids,
            "room's bed should not be available " "because the entire room is reserved",
        )

    def test_not_avail_shared_room_with_one_bed_occupied(self):
        """
        Check that not allow to select a shared
        room with a bed occupied
        ----------------
        Create a room1's bed reservation and check
        that the room1 real avail is not available
        """

        # ARRANGE
        today = fields.date.today()
        tomorrow = fields.date.today() + datetime.timedelta(days=1)

        # ACT
        self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "preferred_room_id": self.r1bed1.id,
                "checkin": today,
                "checkout": tomorrow,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ASSERT
        self.assertNotIn(
            self.room1.id,
            self.pms_property1.with_context(
                checkin=today,
                checkout=tomorrow,
                room_type_id=self.room_type_bed.id,
            ).free_room_ids.ids,
            "Entire Shared room should not be available "
            "becouse it has a bed occupied",
        )

    def test_avail_beds_with_one_bed_occupied(self):
        """
        Check the select of a bed when it has a
        room with other beds occupied
        ----------------
        Create a room1's bed (it has 2 beds) reservation
        and check that the other bed is avail
        """

        # ARRANGE
        today = fields.date.today()
        tomorrow = fields.date.today() + datetime.timedelta(days=1)

        # ACT
        self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "preferred_room_id": self.r1bed1.id,
                "checkin": today,
                "checkout": tomorrow,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ASSERT
        self.assertIn(
            self.r1bed2.id,
            self.pms_property1.with_context(
                checkin=today,
                checkout=tomorrow,
                room_type_id=self.room_type_bed.id,
            ).free_room_ids.ids,
            "The bed2 of the shared room should be available",
        )

    def test_not_allowed_reservation_in_bed_with_room_occuppied(self):
        """
        Check the constrain that not allow to create a reservation in a bed in a
        room with other reservation like shared
        ----------------
        Create a room1's reservation and the try to create a reservation
        in the room1's bed, we expect an error
        """

        # ARRANGE
        today = fields.date.today()
        tomorrow = fields.date.today() + datetime.timedelta(days=1)

        self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "preferred_room_id": self.room1.id,
                "checkin": today,
                "checkout": tomorrow,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ACT & ASSERT
        with self.assertRaises(
            ValidationError,
            msg="Reservation created on a bed whose room was already occupied",
        ):
            r_test = self.env["pms.reservation"].create(
                {
                    "partner_id": self.partner1.id,
                    "preferred_room_id": self.r1bed1.id,
                    "checkin": today,
                    "checkout": tomorrow,
                    "pms_property_id": self.pms_property1.id,
                    "sale_channel_origin_id": self.sale_channel_direct1.id,
                }
            )
            r_test.flush_recordset()

    def test_not_allowed_reservation_in_shared_room_with_bed_occuppied(self):
        """
        Check the constrain that not allow to create a reservation
        in a shared room in a bed reservation
        ----------------
        Create a room1's bed reservation and the try to create
        a reservation in the room1, we expect an error
        """

        # ARRANGE
        today = fields.date.today()
        tomorrow = fields.date.today() + datetime.timedelta(days=1)

        self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "preferred_room_id": self.r1bed1.id,
                "checkin": today,
                "checkout": tomorrow,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ACT & ASSERT
        with self.assertRaises(
            ValidationError,
            msg="Reservation created in a full shared "
            "room that already had beds occupied",
        ):
            r_test = self.env["pms.reservation"].create(
                {
                    "partner_id": self.partner1.id,
                    "preferred_room_id": self.room1.id,
                    "checkin": today,
                    "checkout": tomorrow,
                    "pms_property_id": self.pms_property1.id,
                    "sale_channel_origin_id": self.sale_channel_direct1.id,
                }
            )
            r_test.flush_recordset()

    def check_room_shared_availability_released_when_canceling_bed_reservations(self):
        """
        Check that check availability in shared room is
        released when canceling bed reservations
        ----------------
        Create a room1's bed reservation and then cancel it,
        check that the room1 real avail is 1
        """

        # ARRANGE
        today = fields.date.today()
        tomorrow = fields.date.today() + datetime.timedelta(days=1)

        # ACT
        r1 = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "preferred_room_id": self.r1bed1.id,
                "checkin": today,
                "checkout": tomorrow,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r1.action_cancel()

        # ASSERT
        self.assertEqual(
            self.pms_property1.with_context(
                checkin=today,
                checkout=tomorrow,
                room_type_id=self.room_type_test.id,
            ).availability,
            1,
            "The parent room avail dont update " "when cancel child room reservation",
        )

    def check_bed_availability_released_when_canceling_parent_room_reservations(self):
        """
        Check that check availability in child room is
        released when canceling the parent rooms
        ----------------
        Create a room1 reservation and then cancel it,
        check that the beds real avail is 2
        """

        # ARRANGE
        today = fields.date.today()
        tomorrow = fields.date.today() + datetime.timedelta(days=1)

        # ACT
        r1 = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "preferred_room_id": self.room1.id,
                "checkin": today,
                "checkout": tomorrow,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r1.action_cancel()

        # ASSERT
        self.assertEqual(
            self.pms_property1.with_context(
                checkin=today,
                checkout=tomorrow,
                room_type_id=self.room_type_bed.id,
            ).availability,
            2,
            "The child room avail dont update when " "cancel parent room reservation",
        )
