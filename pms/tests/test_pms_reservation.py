import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import ValidationError

from .common import TestHotel


@freeze_time("2012-01-14")
class TestPmsReservations(TestHotel):
    def create_common_scenario(self):
        # create a room type availability
        self.room_type_availability = self.env[
            "pms.room.type.availability.plan"
        ].create({"name": "Availability plan for TEST"})

        # create a property
        self.property = self.env["pms.property"].create(
            {
                "name": "MY PMS TEST",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
            }
        )

        # create room type class
        self.room_type_class = self.env["pms.room.type.class"].create(
            {"name": "Room", "code_class": "ROOM"}
        )

        # create room type
        self.room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.property.id],
                "name": "Double Test",
                "code_type": "DBL_Test",
                "class_id": self.room_type_class.id,
            }
        )

        # create rooms
        self.room1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.property.id,
                "name": "Double 101",
                "room_type_id": self.room_type_double.id,
                "capacity": 2,
            }
        )

        self.room2 = self.env["pms.room"].create(
            {
                "pms_property_id": self.property.id,
                "name": "Double 102",
                "room_type_id": self.room_type_double.id,
                "capacity": 2,
            }
        )

        self.room3 = self.env["pms.room"].create(
            {
                "pms_property_id": self.property.id,
                "name": "Double 103",
                "room_type_id": self.room_type_double.id,
                "capacity": 2,
            }
        )
        self.demo_user = self.env.ref("base.user_admin")

    @freeze_time("1980-11-01")
    def test_create_reservation_start_date(self):
        # TEST CASE
        # reservation should start on checkin day

        # ARRANGE
        today = fields.date.today()
        checkin = today + datetime.timedelta(days=8)
        checkout = checkin + datetime.timedelta(days=11)
        customer = self.env.ref("base.res_partner_12")
        reservation_vals = {
            "checkin": checkin,
            "checkout": checkout,
            "room_type_id": self.room_type_3.id,
            "partner_id": customer.id,
            "pms_property_id": self.main_hotel_property.id,
        }

        # ACT
        reservation = self.env["pms.reservation"].create(reservation_vals)

        self.assertEqual(
            reservation.reservation_line_ids[0].date,
            checkin,
            "Reservation lines don't start in the correct date",
        )

    @freeze_time("1980-11-01")
    def test_create_reservation_end_date(self):
        # TEST CASE
        # reservation should end on checkout day

        # ARRANGE
        today = fields.date.today()
        checkin = today + datetime.timedelta(days=8)
        checkout = checkin + datetime.timedelta(days=11)
        customer = self.env.ref("base.res_partner_12")
        reservation_vals = {
            "checkin": checkin,
            "checkout": checkout,
            "room_type_id": self.room_type_3.id,
            "partner_id": customer.id,
            "pms_property_id": self.main_hotel_property.id,
        }

        # ACT
        reservation = self.env["pms.reservation"].create(reservation_vals)

        self.assertEqual(
            reservation.reservation_line_ids[-1].date,
            checkout - datetime.timedelta(1),
            "Reservation lines don't end in the correct date",
        )

    @freeze_time("1980-11-01")
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
        self.create_common_scenario()

        # ACT
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
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

    @freeze_time("1980-11-01")
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
        self.create_common_scenario()

        # ACT
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
            }
        )
        r_test.flush()

        # ASSERT
        self.assertFalse(r_test.splitted, "The reservation shouldn't be splitted")

    @freeze_time("1980-11-01")
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
        self.create_common_scenario()

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
            }
        )
        r1.reservation_line_ids[0].room_id = self.room2.id
        r1.flush()

        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
            }
        )
        r2.reservation_line_ids[0].room_id = self.room3.id
        r2.flush()

        r3 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=1),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
            }
        )
        r3.reservation_line_ids[0].room_id = self.room1.id
        r3.flush()

        r4 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=1),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
            }
        )
        r4.reservation_line_ids[0].room_id = self.room3.id
        r4.flush()
        expected_num_changes = 2

        # ACT
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=4),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
            }
        )
        r_test.flush()

        # ASSERT
        self.assertEqual(
            expected_num_changes,
            len(r_test.reservation_line_ids.mapped("room_id")),
            "The reservation shouldn't have more than 2 changes",
        )

    @freeze_time("1980-11-01")
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
        self.create_common_scenario()

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
            }
        )
        r1.reservation_line_ids[0].room_id = self.room2.id
        r1.flush()

        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
            }
        )
        r2.reservation_line_ids[0].room_id = self.room3.id
        r2.flush()

        r3 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=1),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
            }
        )
        r3.reservation_line_ids[0].room_id = self.room1.id
        r3.flush()

        r4 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=1),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
            }
        )
        r4.reservation_line_ids[0].room_id = self.room3.id
        r4.flush()

        r5 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=2),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
            }
        )
        r5.reservation_line_ids[0].room_id = self.room2.id
        r5.flush()

        # ACT
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=4),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
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

    @freeze_time("1980-11-01")
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
        self.create_common_scenario()

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
            }
        )
        r1.reservation_line_ids[0].room_id = self.room1
        r1.flush()

        # ACT & ASSERT
        with self.assertRaises(ValidationError):
            r_test = self.env["pms.reservation"].create(
                {
                    "pms_property_id": self.property.id,
                    "checkin": datetime.datetime.now(),
                    "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                    "adults": 2,
                    "preferred_room_id": self.room1.id,
                }
            )
            r_test.flush()

    @freeze_time("1980-11-01")
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
        self.create_common_scenario()

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
            }
        )
        r1.reservation_line_ids[0].room_id = self.room1
        r1.reservation_line_ids[1].room_id = self.room1
        r1.flush()

        # ACT & ASSERT
        with self.assertRaises(ValidationError):
            r_test = self.env["pms.reservation"].create(
                {
                    "pms_property_id": self.property.id,
                    "checkin": datetime.datetime.now() + datetime.timedelta(days=1),
                    "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                    "adults": 2,
                    "preferred_room_id": self.room1.id,
                }
            )
            r_test.flush()

    @freeze_time("1980-11-01")
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
        self.create_common_scenario()

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
            }
        )
        r1.reservation_line_ids[0].room_id = self.room1
        r1.reservation_line_ids[1].room_id = self.room1
        r1.reservation_line_ids[2].room_id = self.room1
        r1.flush()

        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
            }
        )
        r2.reservation_line_ids[0].room_id = self.room2
        r2.reservation_line_ids[1].room_id = self.room2
        r2.reservation_line_ids[2].room_id = self.room2
        r2.flush()

        r3 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
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
                    "pms_property_id": self.property.id,
                    "checkin": datetime.datetime.now(),
                    "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                    "adults": 2,
                    "room_type_id": self.room_type_double.id,
                }
            )

    def test_manage_children_raise(self):
        # TEST CASE
        # reservation with 2 adults and 1 children occupyin
        # shouldn be higher than room capacity
        # the capacity for xid pms.pms_room_type_0 is 2 in demo data
        # NO ARRANGE
        # ACT & ASSERT
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env["pms.reservation"].create(
                {
                    "adults": 2,
                    "children_occupying": 1,
                    "checkin": datetime.datetime.now(),
                    "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                    "room_type_id": self.browse_ref("pms.pms_room_type_0").id,
                }
            )

    @freeze_time("1981-11-01")
    def test_order_priority_to_assign(self):
        # ARRANGE
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "pms_property_id": self.property.id,
            }
        )
        self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "pms_property_id": self.property.id,
            }
        )
        r1.to_assign = False
        # ACT
        reservations = self.env["pms.reservation"].search(
            [("pms_property_id", "=", self.property.id)]
        )
        # ASSERT
        self.assertEqual(r1, reservations[0])

    @freeze_time("1981-11-01")
    def test_order_priority_left_for_checkin(self):
        # ARRANGE
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "pms_property_id": self.property.id,
            }
        )
        self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "pms_property_id": self.property.id,
            }
        )
        r1.left_for_checkin = False
        # ACT
        reservations = self.env["pms.reservation"].search(
            [("pms_property_id", "=", self.property.id)]
        )
        # ASSERT
        self.assertEqual(r1, reservations[0])

    @freeze_time("1981-11-01")
    def test_order_priority_left_for_checkout(self):
        # ARRANGE
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "pms_property_id": self.property.id,
            }
        )
        self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "pms_property_id": self.property.id,
            }
        )
        r1.left_for_checkout = True
        # ACT
        reservations = self.env["pms.reservation"].search(
            [("pms_property_id", "=", self.property.id)]
        )
        # ASSERT
        self.assertEqual(r1, reservations[0])

    @freeze_time("1981-11-01")
    def test_order_priority_state_onboard_and_pending_amount(self):
        # ARRANGE
        self.create_common_scenario()
        host = self.env["res.partner"].create(
            {
                "name": "Miguel",
                "phone": "654667733",
                "email": "miguel@example.com",
            }
        )
        r1 = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "room_type_id": self.room_type_double.id,
                "partner_id": host.id,
                "pms_property_id": self.property.id,
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
        self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "pms_property_id": self.property.id,
            }
        )
        # ACT
        reservations = self.env["pms.reservation"].search(
            [("pms_property_id", "=", self.property.id)]
        )
        # ASSERT
        self.assertEqual(r1, reservations[0])

    @freeze_time("1981-11-01")
    def test_reservation_action_assign(self):
        # TEST CASE
        # the reservation action assign
        # change the reservation to 'to_assign' = False
        # ARRANGE
        self.create_common_scenario()
        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "pms_property_id": self.property.id,
            }
        )
        # ACT
        res.action_assign()
        # ASSERT
        self.assertFalse(res.to_assign, "The reservation should be marked as assigned")

    @freeze_time("1981-11-01")
    def test_reservation_action_cancel(self):
        # TEST CASE
        # the reservation action cancel
        # change the state of the reservation to 'cancelled'
        # ARRANGE
        self.create_common_scenario()
        res = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "pms_property_id": self.property.id,
            }
        )
        # ACT
        res.action_cancel()
        # ASSERT
        self.assertEqual(res.state, "cancelled", "The reservation should be cancelled")

    @freeze_time("1981-11-01")
    def test_reservation_action_checkout(self):
        # TEST CASE
        # the reservation action checkout
        # change the state of the reservation to 'done'
        # ARRANGE
        self.create_common_scenario()
        host = self.env["res.partner"].create(
            {
                "name": "Miguel",
                "phone": "654667733",
                "email": "miguel@example.com",
            }
        )
        r1 = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "room_type_id": self.room_type_double.id,
                "partner_id": host.id,
                "pms_property_id": self.property.id,
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
        r1.action_reservation_checkout()

        # ASSERT
        self.assertEqual(
            r1.state, "done", "The reservation status should be done after checkout."
        )
