import datetime

from odoo import fields

from .common import TestPms


class TestPmsSharedRoom(TestPms):
    def setUp(self):
        super().setUp()
        # create a room type availability
        self.room_type_availability = self.env["pms.availability.plan"].create(
            {
                "name": "Availability plan for TEST",
                "pms_pricelist_ids": [(6, 0, [self.pricelist1.id])],
            }
        )

        self.bed_class = self.env["pms.room.type.class"].create(
            {
                "name": "Bed Class 1",
                "default_code": "B1",
            }
        )

        # create room type
        self.room_type_shared = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Shared Test",
                "default_code": "SHT",
                "class_id": self.room_type_class1.id,
            }
        )

        self.room_type_bed = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Bed Type Test",
                "default_code": "BTT",
                "class_id": self.bed_class.id,
            }
        )

        # create shared room
        self.room1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Shared 101",
                "room_type_id": self.room_type_shared.id,
                "capacity": 2,
                "extra_beds_allowed": 1,
            }
        )

        # create beds in room1
        self.r1bed1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "101 (1)",
                "room_type_id": self.room_type_bed.id,
                "capacity": 1,
                "parent_id": self.room1.id,
            }
        )

        self.r1bed2 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "101 (2)",
                "room_type_id": self.room_type_bed.id,
                "capacity": 2,
                "parent_id": self.room1.id,
            }
        )

        # create partner
        self.partner1 = self.env["res.partner"].create(
            {
                "firstname": "Jaime",
                "lastname": "García",
                "email": "jaime@example.com",
                "birthdate_date": "1983-03-01",
                "gender": "male",
            }
        )

    def test_not_avail_beds_with_room_occupied(self):
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

    def test_not_avail_shared_room_with_one_bed_occupied(self):
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
            }
        )

        # ASSERT
        self.assertEqual(
            self.pms_property1.with_context(
                checkin=today,
                checkout=tomorrow,
                room_type_id=self.room_type_shared.id,
            ).availability,
            0,
            "Shared Room avaialbility should be 0 if it has a bed occupied",
        )

    def test_avail_beds_with_one_bed_occupied(self):
        """
        Check the avail of a bed when it has a room with other beds occupied
        ----------------
        Create a room1's bed (it has 2 beds) reservation and check that the beds avail = 1
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
            }
        )

        # ASSERT
        self.assertEqual(
            self.pms_property1.with_context(
                checkin=today,
                checkout=tomorrow,
                room_type_id=self.room_type_bed.id,
            ).availability,
            1,
            "Shared Room avaialbility should be 0 if it has a bed occupied",
        )
