import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import UserError, ValidationError

from .common import TestPms


class TestPmsReservations(TestPms):
    def setUp(self):
        super().setUp()
        # create a room type availability
        self.room_type_availability = self.env["pms.availability.plan"].create(
            {
                "name": "Availability plan for TEST",
                "pms_pricelist_ids": [(6, 0, [self.pricelist1.id])],
            }
        )

        # create room type
        self.room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )

        # create rooms
        self.room1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Double 101",
                "room_type_id": self.room_type_double.id,
                "capacity": 2,
            }
        )

        self.room2 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Double 102",
                "room_type_id": self.room_type_double.id,
                "capacity": 2,
            }
        )

        self.room3 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Double 103",
                "room_type_id": self.room_type_double.id,
                "capacity": 2,
            }
        )
        self.partner1 = self.env["res.partner"].create(
            {
                "firstname": "Jaime",
                "lastname": "García",
                "email": "jaime@example.com",
                "birthdate_date": "1983-03-01",
                "gender": "male",
            }
        )
        self.id_category = self.env["res.partner.id_category"].create(
            {"name": "DNI", "code": "D"}
        )

    def test_reservation_dates_not_consecutive(self):
        """
        Check the constrain if not consecutive dates
        ----------------
        Create correct reservation set 3 reservation lines consecutives (nights)
        """
        # ARRANGE
        today = fields.date.today()
        tomorrow = fields.date.today() + datetime.timedelta(days=1)
        three_days_later = fields.date.today() + datetime.timedelta(days=3)

        # ACT & ASSERT
        with self.assertRaises(
            ValidationError,
            msg="Error, it has been allowed to create a reservation with non-consecutive days",
        ):
            self.env["pms.reservation"].create(
                {
                    "room_type_id": self.room_type_double.id,
                    "partner_id": self.partner1.id,
                    "pms_property_id": self.pms_property1.id,
                    "reservation_line_ids": [
                        (0, False, {"date": today}),
                        (0, False, {"date": tomorrow}),
                        (0, False, {"date": three_days_later}),
                    ],
                }
            )

    def test_reservation_dates_compute_checkin_out(self):
        """
        Check the reservation creation with specific reservation lines
        anc compute checkin checkout
        ----------------
        Create reservation with correct reservation lines and check
        the checkin and checkout fields. Take into account that the
        checkout of the reservation must be the day after the last night
        (view checkout assertEqual)
        """
        # ARRANGE
        today = fields.date.today()
        tomorrow = fields.date.today() + datetime.timedelta(days=1)
        two_days_later = fields.date.today() + datetime.timedelta(days=2)

        # ACT
        reservation = self.env["pms.reservation"].create(
            {
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "reservation_line_ids": [
                    (0, False, {"date": today}),
                    (0, False, {"date": tomorrow}),
                    (0, False, {"date": two_days_later}),
                ],
            }
        )

        # ASSERT
        self.assertEqual(
            reservation.checkin,
            today,
            "The calculated checkin of the reservation does \
            not correspond to the first day indicated in the dates",
        )
        self.assertEqual(
            reservation.checkout,
            two_days_later + datetime.timedelta(days=1),
            "The calculated checkout of the reservation does \
            not correspond to the last day indicated in the dates",
        )

    def test_create_reservation_start_date(self):
        """
        Check that the reservation checkin and the first reservation date are equal.
        ----------------
        Create a reservation and check if the first reservation line date are the same
        date that the checkin date.
        """
        # reservation should start on checkin day

        # ARRANGE
        today = fields.date.today()
        checkin = today + datetime.timedelta(days=8)
        checkout = checkin + datetime.timedelta(days=11)
        reservation_vals = {
            "checkin": checkin,
            "checkout": checkout,
            "room_type_id": self.room_type_double.id,
            "partner_id": self.partner1.id,
            "pms_property_id": self.pms_property1.id,
        }

        # ACT
        reservation = self.env["pms.reservation"].create(reservation_vals)

        self.assertEqual(
            reservation.reservation_line_ids[0].date,
            checkin,
            "Reservation lines don't start in the correct date",
        )

    def test_create_reservation_end_date(self):
        """
        Check that the reservation checkout and the last reservation date are equal.
        ----------------
        Create a reservation and check if the last reservation line date are the same
        date that the checkout date.
        """
        # ARRANGE
        today = fields.date.today()
        checkin = today + datetime.timedelta(days=8)
        checkout = checkin + datetime.timedelta(days=11)
        reservation_vals = {
            "checkin": checkin,
            "checkout": checkout,
            "room_type_id": self.room_type_double.id,
            "partner_id": self.partner1.id,
            "pms_property_id": self.pms_property1.id,
        }

        # ACT
        reservation = self.env["pms.reservation"].create(reservation_vals)

        self.assertEqual(
            reservation.reservation_line_ids[-1].date,
            checkout - datetime.timedelta(1),
            "Reservation lines don't end in the correct date",
        )

    def test_split_reservation01(self):
        """
        # TEST CASE
        The reservation shouldn't be splitted
        preferred_room_id with availability provided
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 | test | test | test |    |    |    |
        | Double 102 |      |      |      |    |    |    |
        | Double 103 |      |      |      |    |    |    |
        +------------+------+------+------+----+----+----+
        """
        # ARRANGE

        # ACT
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
            }
        )
        r_test.flush()

        # ASSERT
        self.assertTrue(
            all(
                elem.room_id.id == r_test.reservation_line_ids[0].room_id.id
                for elem in r_test.reservation_line_ids
            ),
            "The entire reservation should be allocated in the preferred room",
        )

    def test_split_reservation02(self):
        """
        # TEST CASE
        The reservation shouldn't be splitted
        room_type_id with availability provided
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 | test | test | test |    |    |    |
        | Double 102 |      |      |      |    |    |    |
        | Double 103 |      |      |      |    |    |    |
        +------------+------+------+------+----+----+----+
        """
        # ARRANGE

        # ACT
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
            }
        )
        r_test.flush()

        # ASSERT
        self.assertFalse(r_test.splitted, "The reservation shouldn't be splitted")

    def test_split_reservation03(self):
        """
        # TEST CASE
        The reservation should be splitted in 2 rooms
            (there is only one better option on day 02 and a draw the next day.
             The night before should be prioritized)
        +------------+------+------+------+------+----+----+
        | room/date  |  01  |  02  |  03  | 04   | 05 | 06 |
        +------------+------+------+------+------+----+----+
        | Double 101 | test |  r3  |      |      |    |    |
        | Double 102 |  r1  | test | test | test |    |    |
        | Double 103 |  r2  |  r4  |      |      |    |    |
        +------------+------+------+------+------+----+----+
        """
        # ARRANGE

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
            }
        )
        r1.reservation_line_ids[0].room_id = self.room2.id
        r1.flush()

        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
            }
        )
        r2.reservation_line_ids[0].room_id = self.room3.id
        r2.flush()

        r3 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=1),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
            }
        )
        r3.reservation_line_ids[0].room_id = self.room1.id
        r3.flush()

        r4 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=1),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
            }
        )
        r4.reservation_line_ids[0].room_id = self.room3.id
        r4.flush()
        expected_num_changes = 2

        # ACT
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=4),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
            }
        )
        r_test.flush()
        # ASSERT
        self.assertEqual(
            expected_num_changes,
            len(r_test.reservation_line_ids.mapped("room_id")),
            "The reservation shouldn't have more than 2 changes",
        )

    def test_split_reservation04(self):
        """
        # TEST CASE
        The reservation should be splitted in 3 rooms
            (there are 2 best options on day 03 and room of last night is not available)
        +------------+------+------+------+------+----+----+
        | room/date  |  01  |  02  |  03  | 04   | 05 | 06 |
        +------------+------+------+------+------+----+----+
        | Double 101 | test |  r3  | test | test |    |    |
        | Double 102 |  r1  | test |  r5  |      |    |    |
        | Double 103 |  r2  |  r4  |      |      |    |    |
        +------------+------+------+------+------+----+----+
        """
        # ARRANGE

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
            }
        )
        r1.reservation_line_ids[0].room_id = self.room2.id
        r1.flush()

        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
            }
        )
        r2.reservation_line_ids[0].room_id = self.room3.id
        r2.flush()

        r3 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=1),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
            }
        )
        r3.reservation_line_ids[0].room_id = self.room1.id
        r3.flush()

        r4 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=1),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
            }
        )
        r4.reservation_line_ids[0].room_id = self.room3.id
        r4.flush()

        r5 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=2),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
            }
        )
        r5.reservation_line_ids[0].room_id = self.room2.id
        r5.flush()

        # ACT
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=4),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
            }
        )
        r_test.flush()

        rooms = 0
        last_room = None
        for line in r_test.reservation_line_ids:
            if line.room_id != last_room:
                last_room = line.room_id
                rooms += 1

        # ASSERT
        self.assertEqual(
            3, rooms, "The reservation shouldn't be splitted in more than 3 roomss"
        )

    def test_split_reservation05(self):
        """
        # TEST CASE
        The preferred room_id is not available
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |r1/tst|      |      |    |    |    |
        | Double 102 |      |      |      |    |    |    |
        | Double 103 |      |      |      |    |    |    |
        +------------+------+------+------+----+----+----+
        """
        # ARRANGE

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
            }
        )
        r1.reservation_line_ids[0].room_id = self.room1
        r1.flush()

        # ACT & ASSERT
        with self.assertRaises(ValidationError):
            r_test = self.env["pms.reservation"].create(
                {
                    "pms_property_id": self.pms_property1.id,
                    "checkin": datetime.datetime.now(),
                    "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                    "adults": 2,
                    "preferred_room_id": self.room1.id,
                    "partner_id": self.partner1.id,
                }
            )
            r_test.flush()

    def test_split_reservation06(self):
        """
        # TEST CASE
        There's no availability in the preferred_room_id provided
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r1  |r1/tst|  tst |    |    |    |
        | Double 102 |      |      |      |    |    |    |
        | Double 103 |      |      |      |    |    |    |
        +------------+------+------+------+----+----+----+
        """
        # ARRANGE

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
            }
        )
        r1.reservation_line_ids[0].room_id = self.room1
        r1.reservation_line_ids[1].room_id = self.room1
        r1.flush()

        # ACT & ASSERT
        with self.assertRaises(ValidationError):
            r_test = self.env["pms.reservation"].create(
                {
                    "pms_property_id": self.pms_property1.id,
                    "checkin": datetime.datetime.now() + datetime.timedelta(days=1),
                    "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                    "adults": 2,
                    "preferred_room_id": self.room1.id,
                    "partner_id": self.partner1.id,
                }
            )
            r_test.flush()

    def test_split_reservation07(self):
        """
        # TEST CASE
        There's no availability
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r1  |  r1  |  r1  |    |    |    |
        | Double 102 |  r2  |  r2  |  r2  |    |    |    |
        | Double 103 |  r3  |  r3  |  r3  |    |    |    |
        +------------+------+------+------+----+----+----+
        """
        # ARRANGE
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
            }
        )
        r1.reservation_line_ids[0].room_id = self.room1
        r1.reservation_line_ids[1].room_id = self.room1
        r1.reservation_line_ids[2].room_id = self.room1
        r1.flush()

        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
            }
        )
        r2.reservation_line_ids[0].room_id = self.room2
        r2.reservation_line_ids[1].room_id = self.room2
        r2.reservation_line_ids[2].room_id = self.room2
        r2.flush()

        r3 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
            }
        )
        r3.reservation_line_ids[0].room_id = self.room3
        r3.reservation_line_ids[1].room_id = self.room3
        r3.reservation_line_ids[2].room_id = self.room3
        r3.flush()

        # ACT & ASSERT
        with self.assertRaises(ValidationError):
            self.env["pms.reservation"].create(
                {
                    "pms_property_id": self.pms_property1.id,
                    "checkin": datetime.datetime.now(),
                    "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                    "adults": 2,
                    "room_type_id": self.room_type_double.id,
                    "partner_id": self.partner1.id,
                }
            )

    def test_manage_children_raise(self):
        # TEST CASE
        """
        Check if the error occurs when trying to put more people than the capacity of the room.
        --------------
         Create a reservation with a double room whose capacity is two and try to create
         it with two adults and a child occupying the room.
        """
        # NO ARRANGE
        # ACT & ASSERT
        with self.assertRaises(
            ValidationError,
            msg="The number of people is lower than the capacity of the room",
        ):
            self.env["pms.reservation"].create(
                {
                    "adults": 2,
                    "children_occupying": 1,
                    "checkin": datetime.datetime.now(),
                    "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                    "room_type_id": self.room_type_double.id,
                    "partner_id": self.partner1.id,
                    "pms_property_id": self.pms_property1.id,
                }
            )

    def test_to_assign_priority_reservation(self):
        """
        To assign reservation must have priority = 1
        ------
        Create a reservation with only room_type (to_assign = True),
        regardless of the rest of the fields the priority must be 1

        NOTE:
        WORK FLOW PRIORITY COMPUTE
        Check reservation priority
        --------
        1 - TO ASSIGN, ARRIVAL DELAYED, DEPARTURE DELAYED (= 1)
        2 - CANCELLED with pending amount (= 2)
        3 - DONE with pending amount (= 3)
        4 - ONBOARD with pending amount (= days for checkout)
        5 - CONFIRM/DRAFT with arrival in less than 3 days (= 2 * days for checkin)
        6 - ONBOARD all paid (= 3 * days for checkout)
        7 - DONE with days from checkout < 1 (= 6)
        8 - CONFIRM/DRAFT with arrival between 3 and 20 days (= 3 * days for checkin)
        9 - CONFIRM/DRAFT with arrival in more than 20 days (= 4 * days for checkin)
        10 - DONE with days from checkout < 15 (= 5 * days from checkout)
        11 - DONE with days from checkout between 15 and 90 included (= 10 * days from checkout)
        12 - DONE with days from checkout > 90 (= 100 * days from checkout)
        """
        # ARRANGE
        expected_priority = 1

        # ACT
        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today() + datetime.timedelta(days=30),
                "checkout": fields.date.today() + datetime.timedelta(days=31),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        computed_priority = res.priority

        # ASSERT
        error_msm = (
            (
                "The priority of a reservation to be assigned \
                should be %d and this is %d"
            )
            % (expected_priority, computed_priority)
        )

        self.assertEqual(
            computed_priority,
            expected_priority,
            error_msm,
        )

    def test_arrival_delayed_priority_reservation(self):
        """
        Arrival delayed reservation must have priority = 1
        ------
        Create a reservation with checkin date yesterday, and without checkin action,
        regardless of the rest of the fields the priority must be 1
        """
        # ARRANGE
        expected_priority = 1
        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today() + datetime.timedelta(days=-1),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )

        # ACT
        res.auto_arrival_delayed()
        computed_priority = res.priority

        # ASSERT
        error_msm = (
            (
                "The priority of a arrival delayed reservation \
                should be %d and this is %d"
            )
            % (expected_priority, computed_priority)
        )

        self.assertEqual(
            computed_priority,
            expected_priority,
            error_msm,
        )

    @freeze_time("1981-11-10")
    def test_departure_delayed_priority_reservation(self):
        """
        To departure delayed reservation must have priority = 1
        ------
        Create a reservation and make the work flow to onboard state,
        using jump dates, we make the reservation should have left yesterday,
        regardless of the rest of the fields the priority must be 1
        """
        # ARRANGE
        expected_priority = 1
        freezer = freeze_time("1981-10-08")
        freezer.start()
        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        host1 = self.env["res.partner"].create(
            {
                "firstname": "Pepe",
                "lastname": "Paz",
                "email": "pepe@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        checkin1 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": host1.id,
                "reservation_id": res.id,
                "document_type": self.id_category.id,
                "document_number": "77156490T",
                "document_expedition_date": fields.date.today()
                + datetime.timedelta(days=665),
            }
        )
        checkin1.action_on_board()
        freezer.stop()

        # ACT
        res.auto_departure_delayed()
        computed_priority = res.priority

        # ASSERT
        error_msm = (
            (
                "The priority of a departure delayed reservation \
                should be %d and this is %d"
            )
            % (expected_priority, computed_priority)
        )

        self.assertEqual(
            computed_priority,
            expected_priority,
            error_msm,
        )

    def test_cancel_pending_amount_priority_reservation(self):
        """
        Cancelled with pending payments reservation must have priority = 2
        ------
        create a reservation and cancel it ensuring that there are
        pending payments in it, the priority must be 2
        """
        # ARRANGE
        expected_priority = 2
        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today() + datetime.timedelta(days=55),
                "checkout": fields.date.today() + datetime.timedelta(days=56),
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )

        # ACT
        res.action_cancel()
        computed_priority = res.priority

        # ASSERT
        error_msm = (
            (
                "The priority of a cancelled reservation with pending amount \
                should be %d and this is %d"
            )
            % (expected_priority, computed_priority)
        )

        self.assertEqual(
            computed_priority,
            expected_priority,
            error_msm,
        )

    @freeze_time("1981-11-10")
    def test_done_with_pending_amountpriority_reservation(self):
        """
        Done with pending amount reservation must have priority = 3
        ------
        Create a reservation and make the work flow to onboard - done state,
        using jump dates, we make the checkout reservation with pending amount,
        regardless of the rest of the fields the priority must be 3
        """
        # ARRANGE
        expected_priority = 3
        freezer = freeze_time("1981-10-08")
        freezer.start()
        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        host1 = self.env["res.partner"].create(
            {
                "firstname": "Pepe",
                "lastname": "Paz",
                "email": "pepe@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        checkin1 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": host1.id,
                "reservation_id": res.id,
                "document_type": self.id_category.id,
                "document_number": "77156490T",
                "document_expedition_date": fields.date.today()
                + datetime.timedelta(days=665),
            }
        )
        checkin1.action_on_board()

        freezer.stop()
        freezer = freeze_time("1981-10-09")
        freezer.start()

        res.action_reservation_checkout()

        # ACT
        res.auto_departure_delayed()
        computed_priority = res.priority
        freezer.stop()

        # ASSERT
        error_msm = (
            (
                "The priority of a done reservation with pending amount\
                should be %d and this is %d"
            )
            % (expected_priority, computed_priority)
        )

        self.assertEqual(
            computed_priority,
            expected_priority,
            error_msm,
        )

    @freeze_time("1981-11-10")
    def test_onboard_with_pending_amount_priority_reservation(self):
        """
        Onboard with pending amount reservation must have priority = days for checkout
        ------
        Create a reservation with 3 nights and make the work flow to onboard,
        using jump dates, we set today in 2 nights before checkout,
        regardless of the rest of the fields the priority must be 2
        """
        # ARRANGE
        expected_priority = 3
        freezer = freeze_time("1981-10-08")
        freezer.start()
        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=3),
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        host1 = self.env["res.partner"].create(
            {
                "firstname": "Pepe",
                "lastname": "Paz",
                "email": "pepe@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        checkin1 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": host1.id,
                "reservation_id": res.id,
                "document_type": self.id_category.id,
                "document_number": "77156490T",
                "document_expedition_date": fields.date.today()
                + datetime.timedelta(days=665),
            }
        )

        # ACT
        checkin1.action_on_board()
        computed_priority = res.priority
        freezer.stop()

        # ASSERT
        error_msm = (
            (
                "The priority of a onboard with payment amount reservation \
                should be %d and this is %d"
            )
            % (expected_priority, computed_priority)
        )

        self.assertEqual(
            computed_priority,
            expected_priority,
            error_msm,
        )

    def test_confirm_arriva_lt_3_days_priority_reservation(self):
        """
        Confirm reservation with arrival in less than 3 days, priority = 2 * days for checkout
        ------
        Create a reservation with checkin date on 2 days
        regardless of the rest of the fields the priority must be 2 * 2 = 4
        """
        # ARRANGE
        expected_priority = 4

        # ACT
        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today() + datetime.timedelta(days=2),
                "checkout": fields.date.today() + datetime.timedelta(days=5),
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        computed_priority = res.priority

        # ASSERT
        error_msm = (
            (
                "The priority of a confirm with less than 3 days for arrival \
                reservation should be %d and this is %d"
            )
            % (expected_priority, computed_priority)
        )

        self.assertEqual(
            computed_priority,
            expected_priority,
            error_msm,
        )

    def test_onboard_all_pay_priority_reservation(self):
        """
        Onboard with all pay reservation must have priority = 3 * days for checkout
        ------
        Create a reservation with 3 nights and make the work flow to onboard,
        using jump dates, we set today in 2 nights before checkout,
        regardless of the rest of the fields the priority must be 3 * 3 = 9
        """
        # ARRANGE
        expected_priority = 9
        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=3),
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        host1 = self.env["res.partner"].create(
            {
                "firstname": "Pepe",
                "lastname": "Paz",
                "email": "pepe@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        checkin1 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": host1.id,
                "reservation_id": res.id,
                "document_type": self.id_category.id,
                "document_number": "77156490T",
                "document_expedition_date": fields.date.today()
                + datetime.timedelta(days=665),
            }
        )

        # ACT
        checkin1.action_on_board()
        # REVIEW: set to 0 the price to avoid make the payment
        # (config account company issues in test)
        res.reservation_line_ids.write({"price": 0})
        computed_priority = res.priority

        # ASSERT
        error_msm = (
            (
                "The priority of onboard all pay reservation \
                should be %d and this is %d"
            )
            % (expected_priority, computed_priority)
        )

        self.assertEqual(
            computed_priority,
            expected_priority,
            error_msm,
        )

    @freeze_time("1981-11-10")
    def test_done_yesterday_all_paid_amountpriority_reservation(self):
        """
        Checkout yesterday without pending amount reservation must have priority = 6
        ------
        Create a reservation and make the work flow to onboard - done state,
        using jump dates, we make the checkout reservation without pending amount,
        and set today 1 day after,
        regardless of the rest of the fields the priority must be 6
        """
        # ARRANGE
        expected_priority = 6
        freezer = freeze_time("1981-10-08")
        freezer.start()
        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        host1 = self.env["res.partner"].create(
            {
                "firstname": "Pepe",
                "lastname": "Paz",
                "email": "pepe@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        checkin1 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": host1.id,
                "reservation_id": res.id,
                "document_type": self.id_category.id,
                "document_number": "77156490T",
                "document_expedition_date": fields.date.today()
                + datetime.timedelta(days=665),
            }
        )
        checkin1.action_on_board()

        freezer.stop()
        freezer = freeze_time("1981-10-09")
        freezer.start()

        res.action_reservation_checkout()
        # REVIEW: set to 0 the price to avoid make the payment
        # (config account company issues in test)
        res.reservation_line_ids.write({"price": 0})

        # ACT
        freezer.stop()
        freezer = freeze_time("1981-10-10")
        freezer.start()

        res.update_daily_priority_reservation()
        computed_priority = res.priority
        freezer.stop()

        # ASSERT
        error_msm = (
            (
                "The priority of a done reservation without pending amount\
                and checkout yesterday should be %d and this is %d"
            )
            % (expected_priority, computed_priority)
        )

        self.assertEqual(
            computed_priority,
            expected_priority,
            error_msm,
        )

    def test_confirm_arriva_bt_3_and_20_days_priority_reservation(self):
        """
        Confirm reservation with arrival between 3 and 20 days, priority = 3 * days for checkout
        ------
        Create a reservation with checkin date on 15 days
        regardless of the rest of the fields the priority must be 3 * 15 = 45
        """
        # ARRANGE
        expected_priority = 45

        # ACT
        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today() + datetime.timedelta(days=15),
                "checkout": fields.date.today() + datetime.timedelta(days=20),
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        computed_priority = res.priority

        # ASSERT
        error_msm = (
            (
                "The priority of a confirm with between 3 and 20 days for arrival \
                reservation should be %d and this is %d"
            )
            % (expected_priority, computed_priority)
        )

        self.assertEqual(
            computed_priority,
            expected_priority,
            error_msm,
        )

    def test_confirm_arrival_more_than_20_days_priority_reservation(self):
        """
        Confirm reservation with arrival more than 20 days, priority = 4 * days for checkout
        ------
        Create a reservation with checkin date on 21 days
        regardless of the rest of the fields the priority must be 4 * 21 = 84
        """
        # ARRANGE
        expected_priority = 84

        # ACT
        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today() + datetime.timedelta(days=21),
                "checkout": fields.date.today() + datetime.timedelta(days=25),
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        computed_priority = res.priority

        # ASSERT
        error_msm = (
            (
                "The priority of a confirm with more than 20 days for arrival \
                reservation should be %d and this is %d"
            )
            % (expected_priority, computed_priority)
        )

        self.assertEqual(
            computed_priority,
            expected_priority,
            error_msm,
        )

    @freeze_time("1981-11-10")
    def test_done_checkout_lt_15_days_before_all_paid_priority_reservation(self):
        """
        Checkout less than 15 days before without pending amount reservation
        must have priority = 5 * days from checkout
        ------
        Create a reservation and make the work flow to onboard - done state,
        using jump dates, we make the checkout reservation without pending amount,
        and set today 6 day after,
        regardless of the rest of the fields the priority must be 6 * 5 = 30
        """
        # ARRANGE
        expected_priority = 30
        freezer = freeze_time("1981-10-09")
        freezer.start()
        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        host1 = self.env["res.partner"].create(
            {
                "firstname": "Pepe",
                "lastname": "Paz",
                "email": "pepe@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        checkin1 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": host1.id,
                "reservation_id": res.id,
                "document_type": self.id_category.id,
                "document_number": "77156490T",
                "document_expedition_date": fields.date.today()
                + datetime.timedelta(days=665),
            }
        )
        checkin1.action_on_board()

        freezer.stop()
        freezer = freeze_time("1981-10-10")
        freezer.start()

        res.action_reservation_checkout()
        # REVIEW: set to 0 the price to avoid make the payment
        # (config account company issues in test)
        res.reservation_line_ids.write({"price": 0})

        # ACT
        freezer.stop()
        freezer = freeze_time("1981-10-16")
        freezer.start()

        res.update_daily_priority_reservation()
        computed_priority = res.priority
        freezer.stop()

        # ASSERT
        error_msm = (
            (
                "The priority of a done reservation without pending amount\
                and checkout less than 15 days before should be %d and this is %d"
            )
            % (expected_priority, computed_priority)
        )

        self.assertEqual(
            computed_priority,
            expected_priority,
            error_msm,
        )

    @freeze_time("1981-11-10")
    def test_done_checkout_bt_30_and_90_days_before_all_paid_priority_reservation(self):
        """
        Checkout between 30 and 90 days before without pending amount reservation
        must have priority = 10 * days from checkout
        ------
        Create a reservation and make the work flow to onboard - done state,
        using jump dates, we make the checkout reservation without pending amount,
        and set today 45 day after,
        regardless of the rest of the fields the priority must be 10 * 45 = 450
        """
        # ARRANGE
        expected_priority = 450
        freezer = freeze_time("1981-10-09")
        freezer.start()
        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        host1 = self.env["res.partner"].create(
            {
                "firstname": "Pepe",
                "lastname": "Paz",
                "email": "pepe@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        checkin1 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": host1.id,
                "reservation_id": res.id,
                "document_type": self.id_category.id,
                "document_number": "77156490T",
                "document_expedition_date": fields.date.today()
                + datetime.timedelta(days=665),
            }
        )
        checkin1.action_on_board()

        freezer.stop()
        freezer = freeze_time("1981-10-10")
        freezer.start()

        res.action_reservation_checkout()
        # REVIEW: set to 0 the price to avoid make the payment
        # (config account company issues in test)
        res.reservation_line_ids.write({"price": 0})

        # ACT
        freezer.stop()
        freezer = freeze_time("1981-11-24")
        freezer.start()

        res.update_daily_priority_reservation()
        computed_priority = res.priority
        freezer.stop()

        # ASSERT
        error_msm = (
            (
                "The priority of a done reservation without pending amount\
                and checkout between 30 and 90 days before should be %d and this is %d"
            )
            % (expected_priority, computed_priority)
        )

        self.assertEqual(
            computed_priority,
            expected_priority,
            error_msm,
        )

    @freeze_time("1981-11-10")
    def test_done_checkout_mt_90_days_before_all_paid_priority_reservation(self):
        """
        Checkout more than 90 days before without pending amount reservation
        must have priority = 100 * days from checkout
        ------
        Create a reservation and make the work flow to onboard - done state,
        using jump dates, we make the checkout reservation without pending amount,
        and set today 91 day after,
        regardless of the rest of the fields the priority must be 100 * 91 = 9100
        """
        # ARRANGE
        expected_priority = 9100
        freezer = freeze_time("1981-10-09")
        freezer.start()
        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "preferred_room_id": self.room2.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        host1 = self.env["res.partner"].create(
            {
                "firstname": "Pepe",
                "lastname": "Paz",
                "email": "pepe@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        checkin1 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": host1.id,
                "reservation_id": res.id,
                "document_type": self.id_category.id,
                "document_number": "77156490T",
                "document_expedition_date": fields.date.today()
                + datetime.timedelta(days=665),
            }
        )
        checkin1.action_on_board()

        freezer.stop()
        freezer = freeze_time("1981-10-10")
        freezer.start()

        res.action_reservation_checkout()
        # REVIEW: set to 0 the price to avoid make the payment
        # (config account company issues in test)
        res.reservation_line_ids.write({"price": 0})

        # ACT
        freezer.stop()
        freezer = freeze_time("1982-01-09")
        freezer.start()

        res.update_daily_priority_reservation()
        computed_priority = res.priority
        freezer.stop()

        # ASSERT
        error_msm = (
            (
                "The priority of a done reservation without pending amount\
                and checkout more than 90 days before should be %d and this is %d"
            )
            % (expected_priority, computed_priority)
        )

        self.assertEqual(
            computed_priority,
            expected_priority,
            error_msm,
        )

    def test_reservation_action_assign(self):
        """
        Checks the correct operation of the assign method
        ---------------
        Create a new reservation with only room_type(autoassign -> to_assign = True),
        and the we call to action_assign method to confirm the assignation
        """
        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        # ACT
        res.action_assign()
        # ASSERT
        self.assertFalse(res.to_assign, "The reservation should be marked as assigned")

    def test_reservation_auto_assign_on_create(self):
        """
        When creating a reservation with a specific room,
        it is not necessary to mark it as to be assigned
        ---------------
        Create a new reservation with specific preferred_room_id,
        "to_assign" should be set to false automatically
        """
        # ARRANGE

        # ACT
        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )

        # ASSERT
        self.assertFalse(
            res.to_assign, "Reservation with preferred_room_id set to to_assign = True"
        )

    def test_reservation_auto_assign_after_create(self):
        """
        When assigning a room manually to a reservation marked "to be assigned",
        this field should be automatically unchecked
        ---------------
        Create a new reservation without preferred_room_id (only room_type),
        "to_assign" is True, then set preferred_room_id and "to_assign" should
        be set to false automatically
        """
        # ARRANGE
        # set the priority of the rooms to control the room chosen by auto assign
        self.room1.sequence = 1
        self.room2.sequence = 2

        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )

        # ACT
        # res shoul be room1 in preferred_room_id (minor sequence)
        res.preferred_room_id = self.room2.id

        # ASSERT
        self.assertFalse(
            res.to_assign,
            "The reservation should be marked as assigned automatically \
            when assigning the specific room",
        )

    def test_reservation_to_assign_on_create(self):
        """
        Check the reservation action assign.
        Create a reservation and change the reservation to 'to_assign' = False
        through action_assign() method
        """
        # ARRANGE
        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        # ACT
        res.action_assign()
        # ASSERT
        self.assertFalse(res.to_assign, "The reservation should be marked as assigned")

    def test_reservation_action_cancel(self):
        """
        Check if the reservation has been cancelled correctly.
        -------------
        Create a reservation and change his state to cancelled
        through the action_cancel() method.
        """
        # ARRANGE
        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        # ACT
        res.action_cancel()
        # ASSERT
        self.assertEqual(res.state, "cancel", "The reservation should be cancelled")

    @freeze_time("1981-11-01")
    def test_reservation_action_checkout(self):
        # TEST CASE
        """
        Check that when the date of a reservation passes, it goes to the 'done' status.
        -------------
        Create a host, a reservation and a check-in partner. Assign the partner and the
        reservation to the check-in partner and after one day of the reservation it
        must be in the 'done' status
        """
        # ARRANGE
        host = self.env["res.partner"].create(
            {
                "name": "Miguel",
                "mobile": "654667733",
                "email": "miguel@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category.id,
                "name": "30065089H",
                "valid_from": datetime.date.today(),
                "partner_id": host.id,
            }
        )
        r1 = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "room_type_id": self.room_type_double.id,
                "partner_id": host.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        r1.flush()
        checkin = self.env["pms.checkin.partner"].create(
            {
                "partner_id": host.id,
                "reservation_id": r1.id,
            }
        )
        checkin.action_on_board()
        checkin.flush()

        # ACT
        with freeze_time("1981-11-02"):
            r1._cache.clear()
            r1.action_reservation_checkout()

        # ASSERT
        self.assertEqual(
            r1.state, "done", "The reservation status should be done after checkout."
        )

    def test_multiproperty_checks(self):
        """
        # TEST CASE
        Multiproperty checks in reservation
        +---------------+------+------+------+----+----+
        |  reservation  |           property1          |
        +---------------+------+------+------+----+----+
        |      room     |           property2          |
        |   room_type   |      property2, property3    |
        | board_service |      property2, property3    |
        |   pricelist   |      property2, property3    |
        +---------------+------+------+------+----+----+
        """
        # ARRANGE
        self.property2 = self.env["pms.property"].create(
            {
                "name": "Property_2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )

        self.property3 = self.env["pms.property"].create(
            {
                "name": "Property_3",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )

        self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Board Service Test",
                "default_code": "CB",
            }
        )
        host = self.env["res.partner"].create(
            {
                "name": "Miguel",
                "mobile": "654667733",
                "email": "miguel@example.com",
            }
        )
        self.reservation_test = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "pms_property_id": self.pms_property1.id,
                "partner_id": host.id,
            }
        )

        room_type_test = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [
                    (4, self.property3.id),
                    (4, self.property2.id),
                ],
                "name": "Single",
                "default_code": "SIN",
                "class_id": self.room_type_class1.id,
                "list_price": 30,
            }
        )

        room = self.env["pms.room"].create(
            {
                "name": "Room 101",
                "pms_property_id": self.property2.id,
                "room_type_id": room_type_test.id,
            }
        )

        pricelist = self.env["product.pricelist"].create(
            {
                "name": "pricelist_test",
                "pms_property_ids": [
                    (4, self.property2.id),
                    (4, self.property3.id),
                ],
            }
        )

        board_service_room_type = self.env["pms.board.service.room.type"].create(
            {
                "pms_board_service_id": self.board_service.id,
                "pms_room_type_id": room_type_test.id,
                "pms_property_ids": [self.property2.id, self.property3.id],
            }
        )
        test_cases = [
            {"preferred_room_id": room.id},
            {"room_type_id": room_type_test.id},
            {"pricelist_id": pricelist.id},
            {"board_service_room_id": board_service_room_type.id},
        ]

        for test_case in test_cases:
            with self.subTest(k=test_case):
                with self.assertRaises(UserError):
                    self.reservation_test.write(test_case)

    def _test_check_date_order(self):
        """
        Check that the date order of a reservation is correct.
        ---------------
        Create a reservation with today's date and then check that the date order is also today
        """
        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=3),
                "partner_id": self.partner1.id,
            }
        )

        reservation.flush()
        self.assertEqual(
            str(reservation.date_order),
            str(fields.date.today()),
            "Date Order isn't correct",
        )

    def _test_check_checkin_datetime(self):
        """
        Check that the checkin datetime of a reservation is correct.
        ------------------
        Create a reservation and then check if the checkin datetime
        it is correct
        """
        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": fields.date.today() + datetime.timedelta(days=300),
                "checkout": fields.date.today() + datetime.timedelta(days=305),
                "partner_id": self.partner1.id,
            }
        )
        r = reservation.checkin
        checkin_expected = datetime.datetime(r.year, r.month, r.day, 14, 00)
        # checkin_expected = checkin_expected.astimezone(self.property.tz.value)

        self.assertEqual(
            str(reservation.checkin_datetime),
            str(checkin_expected),
            "Date Order isn't correct",
        )

    def test_check_allowed_room_ids(self):
        """
        Check available rooms after creating a reservation.
        -----------
        Create an availability rule, create a reservation,
        and then check that the allopwed_room_ids field of the
        reservation and the room_type_id.room_ids field of the
        availability rule match.
        """
        availability_rule = self.env["pms.availability.plan.rule"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type_double.id,
                "availability_plan_id": self.room_type_availability.id,
                "date": fields.date.today() + datetime.timedelta(days=153),
            }
        )
        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": fields.date.today() + datetime.timedelta(days=150),
                "checkout": fields.date.today() + datetime.timedelta(days=152),
                "partner_id": self.partner1.id,
                "room_type_id": self.room_type_double.id,
                "pricelist_id": self.pricelist1.id,
            }
        )
        self.assertEqual(
            reservation.allowed_room_ids,
            availability_rule.room_type_id.room_ids,
            "Rooms allowed don't match",
        )

    def test_partner_is_agency(self):
        """
        Check that a reservation created with an agency and without a partner
        assigns that agency as a partner.
        -------------
        Create an agency and then create a reservation to which that agency
        assigns but does not associate any partner.
        Then check that the partner of that reservation is the same as the agency
        """
        sale_channel1 = self.env["pms.sale.channel"].create(
            {"name": "Test Indirect", "channel_type": "indirect"}
        )
        agency = self.env["res.partner"].create(
            {
                "name": "partner1",
                "is_agency": True,
                "sale_channel_id": sale_channel1.id,
                "invoice_to_agency": True,
            }
        )

        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": fields.date.today() + datetime.timedelta(days=150),
                "checkout": fields.date.today() + datetime.timedelta(days=152),
                "agency_id": agency.id,
            }
        )

        reservation.flush()

        self.assertEqual(
            reservation.partner_id.id,
            agency.id,
            "Partner_id doesn't match with agency_id",
        )

    def test_agency_pricelist(self):
        """
        Check that a pricelist of a reservation created with an
        agency and without a partner and the pricelist of that
        agency are the same.
        -------------
        Create an agency with field apply_pricelist is True and
        then create a reservation to which that agency
        assigns but does not associate any partner.
        Then check that the pricelist of that reservation is the same as the agency
        """
        sale_channel1 = self.env["pms.sale.channel"].create(
            {
                "name": "Test Indirect",
                "channel_type": "indirect",
                "product_pricelist_ids": [(6, 0, [self.pricelist1.id])],
            }
        )
        agency = self.env["res.partner"].create(
            {
                "name": "partner1",
                "is_agency": True,
                "sale_channel_id": sale_channel1.id,
                "apply_pricelist": True,
            }
        )

        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": fields.date.today() + datetime.timedelta(days=150),
                "checkout": fields.date.today() + datetime.timedelta(days=152),
                "agency_id": agency.id,
            }
        )
        self.assertEqual(
            reservation.pricelist_id.id,
            reservation.agency_id.property_product_pricelist.id,
            "Rervation pricelist doesn't match with Agency pricelist",
        )

    def test_compute_access_url(self):
        """
        Check that the access_url field of the reservation is created with a correct value.
        -------------
        Create a reservation and then check that the access_url field has the value
        my/reservation/(reservation.id)
        """
        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": fields.date.today() + datetime.timedelta(days=150),
                "checkout": fields.date.today() + datetime.timedelta(days=152),
                "partner_id": self.partner1.id,
            }
        )

        url = "/my/reservations/%s" % reservation.id
        self.assertEqual(reservation.access_url, url, "Reservation url isn't correct")

    def test_compute_ready_for_checkin(self):
        """
        Check that the ready_for_checkin field is True when the reservation
        checkin day is today.
        ---------------
        Create two hosts, create a reservation with a checkin date today,
        and associate two checkin partners with that reservation and with
        each of the hosts.
        Then check that the ready_for_checkin field of the reservation is True
        """
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Miguel",
                "mobile": "654667733",
                "email": "miguel@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category.id,
                "name": "30065000H",
                "valid_from": datetime.date.today(),
                "partner_id": self.host1.id,
            }
        )
        self.host2 = self.env["res.partner"].create(
            {
                "name": "Brais",
                "mobile": "654437733",
                "email": "brais@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category.id,
                "name": "30065089H",
                "valid_from": datetime.date.today(),
                "partner_id": self.host2.id,
            }
        )
        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": "2012-01-14",
                "checkout": "2012-01-17",
                "partner_id": self.host1.id,
                "allowed_checkin": True,
                "pms_property_id": self.pms_property1.id,
                "adults": 3,
            }
        )
        self.checkin1 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.host1.id,
                "reservation_id": self.reservation.id,
            }
        )
        self.checkin2 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.host2.id,
                "reservation_id": self.reservation.id,
            }
        )

        self.reservation.checkin_partner_ids = [
            (6, 0, [self.checkin1.id, self.checkin2.id])
        ]
        self.assertTrue(
            self.reservation.ready_for_checkin,
            "Reservation should is ready for checkin",
        )

    def test_check_checkout_less_checkin(self):
        """
        Check that a reservation cannot be created with the
        checkin date greater than the checkout date
        ---------------
        Create a reservation with the checkin date 3 days
        after the checkout date, this should throw an error.
        """
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Host1",
            }
        )
        with self.assertRaises(UserError):
            self.env["pms.reservation"].create(
                {
                    "checkin": fields.date.today() + datetime.timedelta(days=3),
                    "checkout": fields.date.today(),
                    "pms_property_id": self.pms_property1.id,
                    "partner_id": self.host1.id,
                }
            )

    def test_check_more_adults_than_beds(self):
        """
        Check that a reservation cannot be created when the field
        adults is greater than the capacity of the room.
        -------------
        Try to create a reservation with a double room and the
        field 'adults'=4, this should throw a mistake because the
        room capacity is lesser than the number of adults.
        """
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Host1",
            }
        )
        with self.assertRaises(ValidationError):
            self.env["pms.reservation"].create(
                {
                    "checkin": fields.date.today(),
                    "checkout": fields.date.today() + datetime.timedelta(days=3),
                    "pms_property_id": self.pms_property1.id,
                    "partner_id": self.host1.id,
                    "room_type_id": self.room_type_double.id,
                    "adults": 4,
                }
            )

    def test_check_format_arrival_hour(self):
        """
        Check that the format of the arrival_hour field is correct(HH:mm)
        -------------
        Create a reservation with the wrong arrival hour date
        format (HH:mm:ss), this should throw an error.
        """
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Host1",
            }
        )
        with self.assertRaises(ValidationError):
            self.env["pms.reservation"].create(
                {
                    "checkin": fields.date.today(),
                    "checkout": fields.date.today() + datetime.timedelta(days=3),
                    "pms_property_id": self.pms_property1.id,
                    "partner_id": self.host1.id,
                    "arrival_hour": "14:00:00",
                }
            )

    def test_check_format_departure_hour(self):
        """
        Check that the format of the departure_hour field is correct(HH:mm)
        -------------
        Create a reservation with the wrong departure hour date
        format (HH:mm:ss), this should throw an error.
        """
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Host1",
            }
        )
        with self.assertRaises(ValidationError):
            self.env["pms.reservation"].create(
                {
                    "checkin": fields.date.today(),
                    "checkout": fields.date.today() + datetime.timedelta(days=3),
                    "pms_property_id": self.pms_property1.id,
                    "partner_id": self.host1.id,
                    "departure_hour": "14:00:00",
                }
            )

    def test_check_property_integrity_room(self):
        """
        Check that a reservation cannot be created with a room
        of a different property.
        ------------
         Try to create a reservation for property2 with a
         preferred_room that belongs to property1, this
         should throw an error .
        """
        self.property2 = self.env["pms.property"].create(
            {
                "name": "MY PMS TEST",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Host1",
            }
        )
        self.room_type_double.pms_property_ids = [
            (6, 0, [self.pms_property1.id, self.property2.id])
        ]
        with self.assertRaises(ValidationError):
            self.env["pms.reservation"].create(
                {
                    "checkin": fields.date.today(),
                    "checkout": fields.date.today() + datetime.timedelta(days=3),
                    "pms_property_id": self.property2.id,
                    "partner_id": self.host1.id,
                    "room_type_id": self.room_type_double.id,
                    "preferred_room_id": self.room1.id,
                }
            )

    def test_shared_folio_true(self):
        """
        Check that the shared_folio field of a reservation whose
        folio has other reservations is True.
        ---------
        Create a reservation and then create another reservation with
        its folio_id = folio_id of the previous reservation. This
        should set shared_folio to True
        """
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Host1",
            }
        )
        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today() + datetime.timedelta(days=60),
                "checkout": fields.date.today() + datetime.timedelta(days=65),
                "pms_property_id": self.pms_property1.id,
                "partner_id": self.host1.id,
            }
        )
        self.reservation2 = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today() + datetime.timedelta(days=60),
                "checkout": fields.date.today() + datetime.timedelta(days=64),
                "pms_property_id": self.pms_property1.id,
                "partner_id": self.host1.id,
                "folio_id": self.reservation.folio_id.id,
            }
        )
        self.assertTrue(
            self.reservation.shared_folio,
            "Folio.reservations > 1, so reservation.shared_folio must be True",
        )

    def test_shared_folio_false(self):
        """
        Check that the shared_folio field for a reservation whose folio has no
        other reservations is False.
        """
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Host1",
            }
        )
        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today() + datetime.timedelta(days=60),
                "checkout": fields.date.today() + datetime.timedelta(days=65),
                "pms_property_id": self.pms_property1.id,
                "partner_id": self.host1.id,
            }
        )
        self.assertFalse(
            self.reservation.shared_folio,
            "Folio.reservations = 1, so reservation.shared_folio must be False",
        )

    def test_reservation_action_cancel_fail(self):
        """
        Check that a reservation cannot be in the cancel state if
        the cancellation is not allowed.
        ---------
         Create a reservation, put its state = "canceled" and then try to
         pass its state to cancel using the action_cancel () method. This
         should throw an error because a reservation with state cancel cannot
         be canceled again.
        """
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Host1",
            }
        )
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.host1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )

        reservation.state = "cancel"

        with self.assertRaises(UserError):
            reservation.action_cancel()

    def test_cancelation_reason_noshow(self):
        """
        Check that if a reservation has already passed and there is no check-in,
        the reason for cancellation must be 'no-show'
        ------
        Create a cancellation rule that is assigned to a pricelist. Then create
        a reservation with a past date and the action_cancel method is launched.
        The canceled_reason field is verified to be is equal to "no_show"
        """
        Pricelist = self.env["product.pricelist"]
        self.cancelation_rule = self.env["pms.cancelation.rule"].create(
            {
                "name": "Cancelation Rule Test",
                "pms_property_ids": [self.pms_property1.id],
                "penalty_noshow": 50,
            }
        )

        self.pricelist = Pricelist.create(
            {
                "name": "Pricelist Test",
                "pms_property_ids": [self.pms_property1.id],
                "cancelation_rule_id": self.cancelation_rule.id,
            }
        )
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Host1",
            }
        )

        reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today() + datetime.timedelta(days=-5),
                "checkout": fields.date.today() + datetime.timedelta(days=-3),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.host1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist.id,
            }
        )

        reservation.action_cancel()
        reservation.flush()
        self.assertEqual(
            reservation.cancelled_reason,
            "noshow",
            "If reservation has already passed and no checkin,"
            "cancelled_reason must be 'noshow'",
        )

    def test_cancelation_reason_intime(self):
        """
        Check that if a reservation is canceled on time according
        to the cancellation rules the canceled_reason field must be "intime"
        ------
        Create a cancellation rule assigned to a price list with
        the field days_intime = 3. Then create a reservation with
        a checkin date within 5 days and launch the action_cancel method.
        canceled_reason field must be "intime"
        """
        Pricelist = self.env["product.pricelist"]
        self.cancelation_rule = self.env["pms.cancelation.rule"].create(
            {
                "name": "Cancelation Rule Test",
                "pms_property_ids": [self.pms_property1.id],
                "days_intime": 3,
            }
        )

        self.pricelist = Pricelist.create(
            {
                "name": "Pricelist Test",
                "pms_property_ids": [self.pms_property1.id],
                "cancelation_rule_id": self.cancelation_rule.id,
            }
        )
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Host1",
            }
        )

        reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today() + datetime.timedelta(days=5),
                "checkout": fields.date.today() + datetime.timedelta(days=8),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.host1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist.id,
            }
        )

        reservation.action_cancel()
        reservation.flush()

        self.assertEqual(
            reservation.cancelled_reason, "intime", "Cancelled reason must be 'intime'"
        )

    def _test_cancelation_reason_late(self):
        """
        Check that if a reservation is canceled outside the cancellation
        period, the canceled_reason field of the reservation must be "late" .
        ---------
        Create a cancellation rule with the days_late = 3 field.
        A reservation is created with a check-in date for tomorrow and the
        action_cancel method is launched. As the reservation was canceled
        after the deadline, the canceled_reason field must be late
        """
        Pricelist = self.env["product.pricelist"]
        self.cancelation_rule = self.env["pms.cancelation.rule"].create(
            {
                "name": "Cancelation Rule Test",
                "pms_property_ids": [self.pms_property1.id],
                "days_late": 3,
            }
        )

        self.pricelist = Pricelist.create(
            {
                "name": "Pricelist Test",
                "pms_property_ids": [self.pms_property1.id],
                "cancelation_rule_id": self.cancelation_rule.id,
            }
        )
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Host1",
            }
        )

        reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today() + datetime.timedelta(days=1),
                "checkout": fields.date.today() + datetime.timedelta(days=4),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.host1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist.id,
            }
        )
        reservation.action_cancel()
        reservation.flush()
        self.assertEqual(reservation.cancelled_reason, "late", "-----------")

    def test_compute_checkin_partner_count(self):
        """
        Check that the number of guests of a reservation is equal
        to the checkin_partner_count field of that same reservation.
        -------------
        Create 2 checkin partners. Create a reservation with those
        two checkin partners. The checkin_partner_count field must
        be equal to the number of checkin partners in the reservation.
        """
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Miguel",
                "mobile": "654667733",
                "email": "miguel@example.com",
            }
        )
        self.host2 = self.env["res.partner"].create(
            {
                "name": "Brais",
                "mobile": "654437733",
                "email": "brais@example.com",
            }
        )
        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": "2013-01-14",
                "checkout": "2013-01-17",
                "partner_id": self.host1.id,
                "pms_property_id": self.pms_property1.id,
                "adults": 3,
            }
        )
        self.checkin1 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.host1.id,
                "reservation_id": self.reservation.id,
            }
        )
        self.checkin2 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.host2.id,
                "reservation_id": self.reservation.id,
            }
        )

        self.reservation.checkin_partner_ids = [
            (6, 0, [self.checkin1.id, self.checkin2.id])
        ]

        self.assertEqual(
            self.reservation.checkin_partner_count,
            len(self.reservation.checkin_partner_ids),
            "Checkin_partner_count must be match with number of checkin_partner_ids",
        )

    def test_compute_checkin_partner_pending_count(self):
        """
        Check that the checkin_partner_count field gives
        the expected result.
        --------------
        Create a reservation with 3 adults and associate 2
        checkin partners with that reservation. The
        checkin_partner_pending_count field must be the
        same as the difference between the adults in the
        reservation and the number of checkin_partner_ids in
        the reservation
        """
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Miguel",
                "mobile": "654667733",
                "email": "miguel@example.com",
            }
        )
        self.host2 = self.env["res.partner"].create(
            {
                "name": "Brais",
                "mobile": "654437733",
                "email": "brais@example.com",
            }
        )
        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": "2014-01-14",
                "checkout": "2014-01-17",
                "partner_id": self.host1.id,
                "pms_property_id": self.pms_property1.id,
                "adults": 3,
            }
        )
        self.checkin1 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.host1.id,
                "reservation_id": self.reservation.id,
            }
        )
        self.checkin2 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.host2.id,
                "reservation_id": self.reservation.id,
            }
        )

        self.reservation.checkin_partner_ids = [
            (6, 0, [self.checkin1.id, self.checkin2.id])
        ]

        count_expected = self.reservation.adults - len(
            self.reservation.checkin_partner_ids
        )
        self.assertEqual(
            self.reservation.checkin_partner_pending_count,
            count_expected,
            "Checkin_partner_pending_count isn't correct",
        )

    def test_reservation_action_checkout_fail(self):
        """
        Check that a reservation cannot be checkout because
        the checkout is not allowed.
        ---------------
        Create a reservation and try to launch the action_reservation_checkout
        method, but this should throw an error, because for the
        checkout to be allowed, the reservation must be in "onboard"
        or "departure_delayed" state
        """
        host = self.env["res.partner"].create(
            {
                "name": "Miguel",
                "mobile": "654667733",
                "email": "miguel@example.com",
            }
        )
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "partner_id": host.id,
                "allowed_checkout": True,
                "pms_property_id": self.pms_property1.id,
            }
        )

        with self.assertRaises(UserError):
            reservation.action_reservation_checkout()

    def test_partner_name_folio(self):
        """
        Check that a reservation without a partner_name
        is associated with the partner_name of its folio
        ----------
        Create a folio with a partner_name. Then create a
        reservation with folio_id = folio.id and without
        partner_name. The partner name of the reservation
        and the folio must be the same
        """

        # ARRANGE
        self.folio1 = self.env["pms.folio"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "partner_name": "Solón",
            }
        )

        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": "2014-01-14",
                "checkout": "2014-01-17",
                "pms_property_id": self.pms_property1.id,
                "folio_id": self.folio1.id,
            }
        )
        # ACT AND ASSERT
        self.assertEqual(
            self.folio1.partner_name,
            self.reservation.partner_name,
            "The folio partner name and the reservation partner name doesn't correspond",
        )

    def test_partner_is_agency_not_invoice_to_agency(self):
        """
        Check that a reservation without partner_name but with
        an agency whose field invoice_to_agency = False will
        be set as partner_name "Reservation_from (agency name)"
        -------------
        Create an agency with invoice_to_agency = False
        and then create a reservation to which that agency
        assigns but does not associate any partner.
        Then check that the partner_name of that reservation is "Reservation from (agency name)"
        """
        sale_channel1 = self.env["pms.sale.channel"].create(
            {"name": "Test Indirect", "channel_type": "indirect"}
        )
        agency = self.env["res.partner"].create(
            {
                "name": "partner1",
                "is_agency": True,
                "sale_channel_id": sale_channel1.id,
            }
        )

        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": fields.date.today() + datetime.timedelta(days=150),
                "checkout": fields.date.today() + datetime.timedelta(days=152),
                "agency_id": agency.id,
            }
        )

        reservation.flush()

        self.assertEqual(
            reservation.partner_name,
            "Reservation from " + agency.name,
            "Partner name doesn't match with to the expected",
        )

    @freeze_time("2010-11-10")
    def test_cancel_discount_board_service(self):
        """
        When a reservation is cancelled, service discount in case of board_services
        must be equal to the discounts of each reservation_line.

        """

        # ARRANGE
        self.cancelation_rule = self.env["pms.cancelation.rule"].create(
            {
                "name": "Cancelation Rule Test",
                "penalty_noshow": 50,
                "apply_on_noshow": "all",
            }
        )

        self.pricelist1.cancelation_rule_id = self.cancelation_rule.id

        self.product = self.env["product.product"].create(
            {
                "name": "Product test",
                "per_day": True,
                "consumed_on": "after",
            }
        )
        self.board_service = self.env["pms.service"].create(
            {
                "is_board_service": True,
                "product_id": self.product.id,
            }
        )

        self.room_type_double.list_price = 25
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today() + datetime.timedelta(days=-3),
                "checkout": fields.date.today() + datetime.timedelta(days=3),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "service_ids": [self.board_service.id],
            }
        )
        # ACTION
        reservation.action_cancel()
        reservation.flush()

        # ASSERT
        self.assertEqual(
            set(reservation.reservation_line_ids.mapped("cancel_discount")),
            set(reservation.service_ids.service_line_ids.mapped("cancel_discount")),
            "Cancel discount of reservation service lines must be the same "
            "that reservation board services",
        )

    @freeze_time("2011-10-10")
    def test_cancel_discount_reservation_line(self):
        """
        When a reservation is cancelled, cancellation discount is given
        by the cancellation rule associated with the reservation pricelist.
        Each reservation_line calculates depending on the cancellation
        reason which is the correspondig discount. In this case the
        cancellation reason is'noshow' and the rule specifies that 50% must
        be reducted every day, that is, on each of reseravtion_lines
        """
        # ARRANGE
        self.cancelation_rule = self.env["pms.cancelation.rule"].create(
            {
                "name": "Cancelation Rule Test",
                "penalty_noshow": 50,
                "apply_on_noshow": "all",
            }
        )

        self.pricelist1.cancelation_rule_id = self.cancelation_rule.id

        self.room_type_double.list_price = 50
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today() + datetime.timedelta(days=-3),
                "checkout": fields.date.today() + datetime.timedelta(days=3),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
            }
        )

        # ACTION
        reservation.action_cancel()
        reservation.flush()

        # ASSERT
        self.assertEqual(
            set(reservation.reservation_line_ids.mapped("cancel_discount")),
            {self.cancelation_rule.penalty_noshow},
            "Cancel discount of reservation_lines must be equal than cancellation rule penalty",
        )

    @freeze_time("2011-11-11")
    def test_cancel_discount_service(self):
        """
        When a reservation is cancelled, service discount in
        services that are not board_services ALWAYS have to be 100%,
        refardless of the cancellation rule associated with the pricelist
        """
        # ARRANGE
        self.cancelation_rule = self.env["pms.cancelation.rule"].create(
            {
                "name": "Cancelation Rule Test",
                "penalty_noshow": 50,
                "apply_on_noshow": "all",
            }
        )

        self.pricelist1.cancelation_rule_id = self.cancelation_rule.id

        self.product = self.env["product.product"].create(
            {
                "name": "Product test",
                "per_day": True,
                "consumed_on": "after",
                "is_extra_bed": True,
            }
        )
        self.service = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": self.product.id,
            }
        )

        reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today() + datetime.timedelta(days=-3),
                "checkout": fields.date.today() + datetime.timedelta(days=3),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "service_ids": [self.service.id],
            }
        )

        expected_cancel_discount = 100

        # ACTION
        reservation.action_cancel()
        reservation.flush()

        # ASSERT
        self.assertEqual(
            {expected_cancel_discount},
            set(reservation.service_ids.service_line_ids.mapped("cancel_discount")),
            "Cancel discount of services must be 100%",
        )

    @freeze_time("2011-06-06")
    def test_discount_in_service(self):
        """
        Discount in pms.service is calculated from the
        discounts that each if its service lines has,
        in this case when reservation is cancelled a
        50% cancellation discount is applied and
        there aren't other different discounts
        """

        # ARRANGE
        self.cancelation_rule = self.env["pms.cancelation.rule"].create(
            {
                "name": "Cancelation Rule Test",
                "penalty_noshow": 50,
                "apply_on_noshow": "all",
            }
        )

        self.pricelist1.cancelation_rule_id = self.cancelation_rule.id

        self.product = self.env["product.product"].create(
            {
                "name": "Product test",
                "per_day": True,
                "consumed_on": "after",
            }
        )
        self.board_service = self.env["pms.service"].create(
            {
                "is_board_service": True,
                "product_id": self.product.id,
            }
        )

        self.room_type_double.list_price = 25
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today() + datetime.timedelta(days=-3),
                "checkout": fields.date.today() + datetime.timedelta(days=3),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "service_ids": [self.board_service.id],
            }
        )

        # ACTION
        reservation.action_cancel()
        reservation.flush()

        expected_discount = sum(
            sl.price_day_total * sl.cancel_discount / 100
            for sl in self.board_service.service_line_ids
        )
        # ASSERT
        self.assertEqual(
            expected_discount,
            self.board_service.discount,
            "Service discount must be the sum of its services_lines discount",
        )

    @freeze_time("2011-11-11")
    def test_services_discount_in_reservation(self):
        """
        Services discount in reservation is equal to the sum of the discounts of all
        its services, whether they are board_services or not
        """
        # ARRANGE
        self.cancelation_rule = self.env["pms.cancelation.rule"].create(
            {
                "name": "Cancelation Rule Test",
                "penalty_noshow": 50,
                "apply_on_noshow": "all",
            }
        )

        self.pricelist1.cancelation_rule_id = self.cancelation_rule.id

        self.product1 = self.env["product.product"].create(
            {
                "name": "Product test1",
                "per_day": True,
                "consumed_on": "after",
                "is_extra_bed": True,
            }
        )
        self.service = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": self.product1.id,
            }
        )
        self.service.flush()
        self.product2 = self.env["product.product"].create(
            {
                "name": "Product test 2",
                "per_person": True,
                "consumed_on": "after",
            }
        )
        self.board_service = self.env["pms.service"].create(
            {
                "is_board_service": True,
                "product_id": self.product2.id,
            }
        )

        self.room_type_double.list_price = 25
        checkin = fields.date.today() + datetime.timedelta(days=-3)
        checkout = fields.date.today() + datetime.timedelta(days=3)
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": checkin,
                "checkout": checkout,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "service_ids": [self.service.id, self.board_service.id],
            }
        )

        # ACTION
        reservation.action_cancel()
        reservation.flush()

        expected_discount = sum(s.discount for s in reservation.service_ids)

        # ASSERT
        self.assertEqual(
            expected_discount,
            reservation.services_discount,
            "Services discount isn't the expected",
        )

    @freeze_time("2011-12-12")
    def test_price_services_in_reservation(self):
        """
        Service price total in a reservation corresponds to the sum of prices
        of all its services less the total discount of that services
        """
        # ARRANGE
        self.cancelation_rule = self.env["pms.cancelation.rule"].create(
            {
                "name": "Cancelation Rule Test",
                "penalty_noshow": 50,
                "apply_on_noshow": "all",
            }
        )

        self.pricelist1.cancelation_rule_id = self.cancelation_rule.id

        self.product1 = self.env["product.product"].create(
            {
                "name": "Product test1",
                "per_day": True,
                "consumed_on": "after",
                "is_extra_bed": True,
            }
        )
        self.service = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": self.product1.id,
            }
        )
        self.service.flush()
        self.product2 = self.env["product.product"].create(
            {
                "name": "Product test 2",
                "per_person": True,
                "consumed_on": "after",
            }
        )
        self.board_service = self.env["pms.service"].create(
            {
                "is_board_service": True,
                "product_id": self.product2.id,
            }
        )

        self.room_type_double.list_price = 25
        checkin = fields.date.today() + datetime.timedelta(days=-3)
        checkout = fields.date.today() + datetime.timedelta(days=3)
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": checkin,
                "checkout": checkout,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "service_ids": [self.service.id, self.board_service.id],
            }
        )

        # ACTION
        reservation.action_cancel()
        reservation.flush()
        expected_price = (
            self.service.price_total
            + self.board_service.price_total * reservation.adults
        ) - reservation.services_discount

        # ASSERT
        self.assertEqual(
            expected_price,
            reservation.price_services,
            "Services price isn't the expected",
        )

    @freeze_time("2011-08-08")
    def test_room_discount_in_reservation(self):
        """
        Discount in pms.reservation is calculated from the
        discounts that each if its reservation lines has,
        in this case when reservation is cancelled a 50%
        cancellation discount is applied and
        there aren't other different discounts
        """
        # ARRANGE
        self.cancelation_rule = self.env["pms.cancelation.rule"].create(
            {
                "name": "Cancelation Rule Test",
                "penalty_noshow": 50,
                "apply_on_noshow": "all",
            }
        )

        self.pricelist1.cancelation_rule_id = self.cancelation_rule.id

        self.room_type_double.list_price = 30
        checkin = fields.date.today() + datetime.timedelta(days=-3)
        checkout = fields.date.today() + datetime.timedelta(days=3)
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": checkin,
                "checkout": checkout,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
            }
        )

        # ACTION
        reservation.action_cancel()
        reservation.flush()

        expected_discount = sum(
            rl.price * rl.cancel_discount / 100
            for rl in reservation.reservation_line_ids
        )

        # ASSERT
        self.assertEqual(
            expected_discount,
            reservation.discount,
            "Room discount isn't the expected",
        )
