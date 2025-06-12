import datetime

from odoo.exceptions import UserError

from .common import TestPms


class TestPmsWizardSplitJoinSwapReservation(TestPms):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # pms.availability.plan
        cls.test_availability_plan = cls.env["pms.availability.plan"].create(
            {
                "name": "Availability plan for TEST",
                "pms_pricelist_ids": [(6, 0, [cls.pricelist1.id])],
            }
        )

        # pms.room.type
        cls.test_room_type_single = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id],
                "name": "Single Test",
                "default_code": "SNG_Test",
                "class_id": cls.room_type_class1.id,
            }
        )
        # pms.room.type
        cls.test_room_type_double = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": cls.room_type_class1.id,
            }
        )

        # create rooms
        cls.room1 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Double 101",
                "room_type_id": cls.test_room_type_double.id,
                "capacity": 2,
            }
        )

        cls.room2 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Double 102",
                "room_type_id": cls.test_room_type_double.id,
                "capacity": 2,
            }
        )

        cls.partner1 = cls.env["res.partner"].create({"name": "Antón"})

        # create a sale channel
        cls.sale_channel_direct1 = cls.env["pms.sale.channel"].create(
            {
                "name": "Door",
                "channel_type": "direct",
            }
        )

    # UNIFY TESTS # review
    def test_unify_reservation_avail_should(self):
        """
        Check that, if there is availability, a reservation with several
        rooms on different days can be unified into a one room reservation.
        ------------
        Create a reservation with room1.Then, in the first reservation line,
        the room is changed to room2.The reservation_join() method of the wizard
        is launched, passing the reservation and room2 as parameters and it is
        verified that room2 is found in all the reservation lines.

        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r1  |      |  r1  |    |    |    |
        | Double 102 |      |  r1  |      |    |    |    |
        +------------+------+------+------+----+----+----+
        """
        # ARRANGE
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r1.flush_recordset()
        r1.reservation_line_ids[0].room_id = self.room2
        # ACT
        self.env["pms.reservation.split.join.swap.wizard"].reservation_join(
            r1, self.room2
        )
        # ASSERT
        self.assertEqual(
            r1.reservation_line_ids.mapped("room_id"),
            self.room2,
            "The unify operation should assign the indicated room to all nights",
        )

    def test_unify_reservation_avail_not(self):
        """
        Check that you cannot unify a reservation with two different rooms
        because there is no availability in the required room.
        ----------
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r1  |  r1  |  r2  |    |    |    |
        | Double 102 |  r0  |  r0  |  r1  |    |    |    |
        +------------+------+------+------+----+----+----+
        """
        # ARRANGE
        self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=2),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.test_room_type_double.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r2.flush_recordset()
        # ACT & ASSERT
        with self.assertRaises(UserError):
            self.env["pms.reservation.split.join.swap.wizard"].reservation_join(
                r1, self.room1
            )

    def test_unify_reservation_avail_not_room_exist(self):
        """
        Check that you cannot unify a reservation with two different rooms
        because there the required room does not exists.
        """

        # ARRANGE

        self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r2.flush_recordset()
        with self.assertRaises(UserError):
            self.env["pms.reservation.split.join.swap.wizard"].reservation_join(
                r2, self.env["pms.room"]
            )

    # SWAP TESTS
    def test_swap_reservation_rooms_01(self):
        # TEST CASE
        """
        Check that the rooms of two different reservations was swapped correctly
        by applying the reservations_swap() method of the wizard.
        ------------
        Initial state
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r1  |  r1  |  r1  |    |    |    |
        | Double 102 |  r2  |  r2  |  r2  |    |    |    |
        +------------+------+------+------+----+----+----+

        State after swap
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r2  |  r2  |  r2  |    |    |    |
        | Double 102 |  r1  |  r1  |  r1  |    |    |    |
        +------------+------+------+------+----+----+----+
        """
        # ARRANGE

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r1.flush_recordset()
        r2.flush_recordset()
        # ACT
        self.env["pms.reservation.split.join.swap.wizard"].reservations_swap(
            datetime.datetime.now(),
            datetime.datetime.now() + datetime.timedelta(days=3),
            self.room1.id,
            self.room2.id,
        )
        # ASSERT
        self.assertTrue(
            r1.reservation_line_ids.room_id == self.room2
            and r2.reservation_line_ids.room_id == self.room1
        )

    def test_swap_reservation_rooms_02(self):
        """
        Check that two rooms from two different reservations are swapped
        correctly.
        -------------------

        Initial state
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |      |  r1  |  r1  |    |    |    |
        | Double 102 |  r2  |  r2  |  r2  |    |    |    |
        +------------+------+------+------+----+----+----+

        State after swap
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r2  |  r2  |  r2  |    |    |    |
        | Double 102 |      |  r1  |  r1  |    |    |    |
        +------------+------+------+------+----+----+----+
        """
        # ARRANGE

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=1),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r1.flush_recordset()
        r2.flush_recordset()
        # ACT
        self.env["pms.reservation.split.join.swap.wizard"].reservations_swap(
            datetime.datetime.now(),
            datetime.datetime.now() + datetime.timedelta(days=3),
            self.room1.id,
            self.room2.id,
        )
        # ASSERT
        self.assertTrue(
            r1.reservation_line_ids.room_id == self.room2
            and r2.reservation_line_ids.room_id == self.room1
        )

    def test_swap_reservation_rooms_03(self):
        """
        Check that two rooms from two different reservations are swapped
        correctly.
        -------------------
        Initial state
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |      |  r1  |  r1  |    |    |    |
        | Double 102 |  r2  |  r2  |  r2  |    |    |    |
        +------------+------+------+------+----+----+----+

        State after swap
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r2  |  r2  |  r2  |    |    |    |
        | Double 102 |      |  r1  |  r1  |    |    |    |
        +------------+------+------+------+----+----+----+
        """
        # ARRANGE

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=1),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r1.flush_recordset()
        r2.flush_recordset()
        # ACT
        self.env["pms.reservation.split.join.swap.wizard"].reservations_swap(
            datetime.datetime.now(),
            datetime.datetime.now() + datetime.timedelta(days=3),
            self.room2.id,
            self.room1.id,
        )
        # ASSERT
        self.assertTrue(
            r1.reservation_line_ids.room_id == self.room2
            and r2.reservation_line_ids.room_id == self.room1
        )

    def test_swap_reservation_rooms_04(self):
        # TEST CASE
        """
        Check that two rooms from two different reservations are swapped
        correctly.
        source: r1
        target: r2
        --------

        Initial state
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r1  |  r1  |      |    |    |    |
        | Double 102 |  r2  |  r2  |  r2  |    |    |    |
        +------------+------+------+------+----+----+----+

        State after swap
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r2  |  r2  |      |    |    |    |
        | Double 102 |  r1  |  r1  |  r2  |    |    |    |
        +------------+------+------+------+----+----+----+
        """
        # ARRANGE

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r1.flush_recordset()
        r2.flush_recordset()
        # ACT
        self.env["pms.reservation.split.join.swap.wizard"].reservations_swap(
            datetime.datetime.now(),
            datetime.datetime.now() + datetime.timedelta(days=3),
            self.room1.id,
            self.room2.id,
        )
        # ASSERT
        self.assertTrue(
            r1.reservation_line_ids.room_id == self.room2
            and r2.reservation_line_ids.room_id == self.room1
        )

    def test_swap_reservation_rooms_05(self):
        """
        Check that two rooms from two different reservations are swapped
        correctly.
        source: r2
        target: r1
        ---------------

        Initial state
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r1  |  r1  |      |    |    |    |
        | Double 102 |  r2  |  r2  |  r2  |    |    |    |
        +------------+------+------+------+----+----+----+

        State after swap
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r2  |  r2  |  r2  |    |    |    |
        | Double 102 |  r1  |  r1  |      |    |    |    |
        +------------+------+------+------+----+----+----+

        """
        # ARRANGE

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r1.flush_recordset()
        r2.flush_recordset()
        # ACT
        self.env["pms.reservation.split.join.swap.wizard"].reservations_swap(
            datetime.datetime.now(),
            datetime.datetime.now() + datetime.timedelta(days=3),
            self.room2.id,
            self.room1.id,
        )
        # ASSERT
        self.assertTrue(
            r1.reservation_line_ids.room_id == self.room2
            and r2.reservation_line_ids.room_id == self.room1
        )

    def test_swap_reservation_rooms_06(self):
        """
        Check that the room is exchanged correctly for every day because there
        is no reservation for another room in those days.
        ---------------------------

        Initial state
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |      |      |      |    |    |    |
        | Double 102 |  r1  |  r1  |  r1  |    |    |    |
        +------------+------+------+------+----+----+----+

        State after swap
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r1  |  r1  |  r1  |    |    |    |
        | Double 102 |      |      |      |    |    |    |
        +------------+------+------+------+----+----+----+
        """
        # ARRANGE

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ACT
        self.env["pms.reservation.split.join.swap.wizard"].reservations_swap(
            datetime.datetime.now(),
            datetime.datetime.now() + datetime.timedelta(days=3),
            self.room2.id,
            self.room1.id,
        )
        # ASSERT
        self.assertTrue(r1.reservation_line_ids.room_id == self.room1)

    def test_swap_reservation_rooms_gap_01(self):
        """
        Check that three rooms from three different reservations are swapped
        correctly.
        -----------

        Initial state
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r0  |      |  r1  |    |    |    |
        | Double 102 |  r2  |  r2  |  r2  |    |    |    |
        +------------+------+------+------+----+----+----+

        State after swap
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r2  |  r2  |  r2  |    |    |    |
        | Double 102 |  r0  |      |  r1  |    |    |    |
        +------------+------+------+------+----+----+----+
        """

        # ARRANGE

        r0 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=2),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r1.flush_recordset()
        r2.flush_recordset()
        # ACT
        self.env["pms.reservation.split.join.swap.wizard"].reservations_swap(
            datetime.datetime.now(),
            datetime.datetime.now() + datetime.timedelta(days=3),
            self.room1.id,
            self.room2.id,
        )
        # ASSERT
        self.assertTrue(
            r0.reservation_line_ids.room_id == self.room2
            and r1.reservation_line_ids.room_id == self.room2
            and r2.reservation_line_ids.room_id == self.room1
        )

    def test_swap_reservation_rooms_gap_02(self):
        # TEST CASE
        """
        Check that three rooms from three different reservations are swapped
        correctly.
        -----------

        Initial state
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r0  |      |  r1  |    |    |    |
        | Double 102 |  r2  |  r2  |  r2  |    |    |    |
        +------------+------+------+------+----+----+----+

        State after swap
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r2  |  r2  |  r2  |    |    |    |
        | Double 102 |  r0  |      |  r1  |    |    |    |
        +------------+------+------+------+----+----+----+
        """
        # ARRANGE

        r0 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=2),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r1.flush_recordset()
        r2.flush_recordset()
        # ACT
        self.env["pms.reservation.split.join.swap.wizard"].reservations_swap(
            datetime.datetime.now(),
            datetime.datetime.now() + datetime.timedelta(days=3),
            self.room2.id,
            self.room1.id,
        )
        # ASSERT
        self.assertTrue(
            r0.reservation_line_ids.room_id == self.room2
            and r1.reservation_line_ids.room_id == self.room2
            and r2.reservation_line_ids.room_id == self.room1
        )

    # NOT VALID TEST CASES
    def test_swap_reservation_not_valid_01(self):
        """
        Check that an error is thrown if you try to pass a room that is
        not reserved for those days to the reservations_swap() method.
        ---------------------------
        Swap room1 with room2 should raise an error because room1 has
        no reservation between checkin & checkout provided.

        Initial state
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |      |      |      |    |    |    |
        | Double 102 |  r1  |  r1  |  r1  |    |    |    |
        +------------+------+------+------+----+----+----+
        """
        # ARRANGE

        self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ASSERT & ACT
        with self.assertRaises(UserError):
            self.env["pms.reservation.split.join.swap.wizard"].reservations_swap(
                datetime.datetime.now(),
                datetime.datetime.now() + datetime.timedelta(days=3),
                self.room1.id,
                self.room2.id,
            )

    # SPLIT TESTS
    def test_split_reservation_check_room_splitted_valid_01(self):
        """
        A reservation is created with preferred room. The room for 1st night
        is switched to another room.
        -------------------

        Expected result:
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |      |  r1  |  r1  |    |    |    |
        | Double 102 |  r1  |      |      |    |    |    |
        +------------+------+------+------+----+----+----+
        """
        # ARRANGE

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r1.flush_recordset()
        # ACT
        self.env["pms.reservation.split.join.swap.wizard"].reservation_split(
            r1, datetime.date.today(), self.room2
        )
        # ASSERT
        self.assertTrue(
            r1.reservation_line_ids[0].room_id == self.room2
            and r1.reservation_line_ids[1:].room_id == self.room1
        )

    def test_split_reservation_check_room_splitted_valid_02(self):
        """
        A reservation is created with preferred room. The room for 1st
        night is switched to another room
        --------------

        Expected result:
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r1  |  r1  |      |    |    |    |
        | Double 102 |      |      |  r1  |    |    |    |
        +------------+------+------+------+----+----+----+
        """
        # ARRANGE

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r1.flush_recordset()
        # ACT
        self.env["pms.reservation.split.join.swap.wizard"].reservation_split(
            r1,
            (
                datetime.datetime(
                    year=datetime.date.today().year,
                    month=datetime.date.today().month,
                    day=datetime.date.today().day,
                )
                + datetime.timedelta(days=2)
            ).date(),
            self.room2,
        )
        # ASSERT
        self.assertTrue(
            r1.reservation_line_ids[2].room_id == self.room2
            and r1.reservation_line_ids[:1].room_id == self.room1
        )

    def test_split_reservation_check_room_splitted_valid_03(self):
        """
        A reservation is created with preferred room. The room for 1st
        night is switched to another room.
        -----------

        Expected result:
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r1  |      |  r1  |    |    |    |
        | Double 102 |      |  r1  |      |    |    |    |
        +------------+------+------+------+----+----+----+"""

        # ARRANGE

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r1.flush_recordset()
        # ACT
        self.env["pms.reservation.split.join.swap.wizard"].reservation_split(
            r1,
            (
                datetime.datetime(
                    year=datetime.date.today().year,
                    month=datetime.date.today().month,
                    day=datetime.date.today().day,
                )
                + datetime.timedelta(days=1)
            ).date(),
            self.room2,
        )
        # ASSERT
        self.assertTrue(
            r1.reservation_line_ids[1].room_id == self.room2
            and r1.reservation_line_ids[0].room_id == self.room1
            and r1.reservation_line_ids[2].room_id == self.room1
        )

    def test_split_reservation_check_room_splitted_not_valid_01(self):
        """
        Try to split the reservation for one night and set with a non valid room.
        ----------
        Create a reservation for room1. Then create a room and it is deleted. The
        reservation_split method is launched but an error should appear because
        the room does not exist.
        """

        # ARRANGE

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r1.flush_recordset()
        room_not_exist = self.room3 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Double 103",
                "room_type_id": self.test_room_type_double.id,
                "capacity": 2,
            }
        )
        room_not_exist.unlink()
        # ACT & ASSERT
        with self.assertRaises(UserError):
            self.env["pms.reservation.split.join.swap.wizard"].reservation_split(
                r1, datetime.datetime.now(), room_not_exist
            )

    def test_split_reservation_check_room_splitted_not_valid_02(self):
        # TEST CASE
        """
        Try to split the reservation for one night and that night
        doesn't belongto reservation.
        ---------------
        A reservation is created with a date interval of 3 days.
        After the reservation_split() method is launched, passing
        that reservation but with a date interval of 100 days,
        this should throw an error.
        """
        # ARRANGE

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r1.flush_recordset()
        # ACT & ASSERT
        with self.assertRaises(UserError):
            self.env["pms.reservation.split.join.swap.wizard"].reservation_split(
                r1, datetime.datetime.now() + datetime.timedelta(days=100), self.room1
            )

    def test_split_reservation_check_room_splitted_not_valid_03(self):
        """
        Try to split the reservation for one night and the reservation
        not exists.
        -------------
        A reservation is created, but it is not the reservation that is
        passed to the reservation_split() method, one that does not exist
        is passed to it, this should throw an error.
        """

        # ARRANGE

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r1.flush_recordset()
        # ACT & ASSERT
        with self.assertRaises(UserError):
            self.env["pms.reservation.split.join.swap.wizard"].reservation_split(
                self.env["pms.reservation"], datetime.datetime.now(), self.room2
            )

    def test_split_reservation_check_room_splitted_not_valid_04(self):
        """
        Try to split the reservation to one room and the room is not available.
        ---------------
        A reservation is created with room2 as favorite_room. Another reservation
        is created for the same days with room1. An attempt is made to separate
        the room from the second reservation using the reservations_split() method,
         passing it the same days as the reservations and room2, but this should
         throw an error because room2 is not available for those days.
        """
        # ARRANGE

        self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r1.flush_recordset()
        # ACT & ASSERT
        with self.assertRaises(UserError):
            self.env["pms.reservation.split.join.swap.wizard"].reservation_split(
                r1, datetime.datetime.now(), self.room2
            )
