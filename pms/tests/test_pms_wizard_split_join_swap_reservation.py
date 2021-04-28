import datetime

from odoo.exceptions import UserError
from odoo.tests import common


class TestPmsWizardMassiveChanges(common.SavepointCase):
    def create_common_scenario(self):
        # product.pricelist
        self.test_pricelist = self.env["product.pricelist"].create(
            {
                "name": "test pricelist 1",
            }
        )
        # pms.availability.plan
        self.test_availability_plan = self.env["pms.availability.plan"].create(
            {
                "name": "Availability plan for TEST",
                "pms_pricelist_ids": [(6, 0, [self.test_pricelist.id])],
            }
        )
        # sequences
        self.folio_sequence = self.env["ir.sequence"].create(
            {
                "name": "PMS Folio",
                "code": "pms.folio",
                "padding": 4,
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        self.reservation_sequence = self.env["ir.sequence"].create(
            {
                "name": "PMS Reservation",
                "code": "pms.reservation",
                "padding": 4,
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        self.checkin_sequence = self.env["ir.sequence"].create(
            {
                "name": "PMS Checkin",
                "code": "pms.checkin.partner",
                "padding": 4,
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        # pms.property
        self.test_property = self.env["pms.property"].create(
            {
                "name": "MY PMS TEST",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.test_pricelist.id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )
        # pms.room.type.class
        self.test_room_type_class = self.env["pms.room.type.class"].create(
            {"name": "Room", "default_code": "ROOM"}
        )

        # pms.room.type
        self.test_room_type_single = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.test_property.id],
                "name": "Single Test",
                "default_code": "SNG_Test",
                "class_id": self.test_room_type_class.id,
            }
        )
        # pms.room.type
        self.test_room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.test_property.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.test_room_type_class.id,
            }
        )

        # create rooms
        self.room1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.test_property.id,
                "name": "Double 101",
                "room_type_id": self.test_room_type_double.id,
                "capacity": 2,
            }
        )

        self.room2 = self.env["pms.room"].create(
            {
                "pms_property_id": self.test_property.id,
                "name": "Double 102",
                "room_type_id": self.test_room_type_double.id,
                "capacity": 2,
            }
        )

        # self.room3 = self.env["pms.room"].create(
        #     {
        #         "pms_property_id": self.test_property.id,
        #         "name": "Double 103",
        #         "room_type_id": self.test_room_type_double.id,
        #         "capacity": 2,
        #     }
        # )

    # UNIFY TESTS # review
    def test_unify_reservation_avail_should(self):
        # TEST CASE
        # Unify reservation in one room with avail for that room
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |  r1  |      |  r1  |    |    |    |
        # | Double 102 |      |  r1  |      |    |    |    |
        # +------------+------+------+------+----+----+----+
        # ARRANGE
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r1.flush()
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
        # TEST CASE
        # Unify reservation in one room and
        # there's not availability for that room

        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |  r1  |  r1  |  r2  |    |    |    |
        # | Double 102 |  r0  |  r0  |  r1  |    |    |    |
        # +------------+------+------+------+----+----+----+
        # ARRANGE
        self.create_common_scenario()
        self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=2),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.test_room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r2.flush()
        # ACT & ASSERT
        with self.assertRaises(UserError):
            self.env["pms.reservation.split.join.swap.wizard"].reservation_join(
                r1, self.room1
            )

    def test_unify_reservation_avail_not_room_exist(self):
        # TEST CASE
        # Unify reservation in one room and
        # the room indicated doesn't exist: pms.room()

        # ARRANGE
        self.create_common_scenario()
        self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r2.flush()
        with self.assertRaises(UserError):
            self.env["pms.reservation.split.join.swap.wizard"].reservation_join(
                r2, self.env["pms.room"]
            )

    # SWAP TESTS
    def test_swap_reservation_rooms_01(self):
        # TEST CASE

        # Initial state
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |  r1  |  r1  |  r1  |    |    |    |
        # | Double 102 |  r2  |  r2  |  r2  |    |    |    |
        # +------------+------+------+------+----+----+----+

        # State after swap
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |  r2  |  r2  |  r2  |    |    |    |
        # | Double 102 |  r1  |  r1  |  r1  |    |    |    |
        # +------------+------+------+------+----+----+----+

        # ARRANGE
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r1.flush()
        r2.flush()
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
        # TEST CASE

        # Initial state
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |      |  r1  |  r1  |    |    |    |
        # | Double 102 |  r2  |  r2  |  r2  |    |    |    |
        # +------------+------+------+------+----+----+----+

        # State after swap
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |      |  r2  |  r2  |    |    |    |
        # | Double 102 |  r2  |  r1  |  r1  |    |    |    |
        # +------------+------+------+------+----+----+----+

        # ARRANGE
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=1),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r1.flush()
        r2.flush()
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
            and r2.reservation_line_ids[1:].room_id == self.room1
        )

    def test_swap_reservation_rooms_03(self):
        # TEST CASE

        # Initial state
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |      |  r1  |  r1  |    |    |    |
        # | Double 102 |  r2  |  r2  |  r2  |    |    |    |
        # +------------+------+------+------+----+----+----+

        # State after swap
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |  r2  |  r2  |  r2  |    |    |    |
        # | Double 102 |      |  r1  |  r1  |    |    |    |
        # +------------+------+------+------+----+----+----+

        # ARRANGE
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=1),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r1.flush()
        r2.flush()
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

        # Initial state
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |  r1  |  r1  |      |    |    |    |
        # | Double 102 |  r2  |  r2  |  r2  |    |    |    |
        # +------------+------+------+------+----+----+----+

        # State after swap
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |  r2  |  r2  |      |    |    |    |
        # | Double 102 |  r1  |  r1  |  r2  |    |    |    |
        # +------------+------+------+------+----+----+----+

        # ARRANGE
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r1.flush()
        r2.flush()
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
            and r2.reservation_line_ids[:1].room_id == self.room1
        )

    def test_swap_reservation_rooms_05(self):
        # TEST CASE

        # Initial state
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |  r1  |  r1  |      |    |    |    |
        # | Double 102 |  r2  |  r2  |  r2  |    |    |    |
        # +------------+------+------+------+----+----+----+

        # State after swap
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |  r2  |  r2  |  r2  |    |    |    |
        # | Double 102 |  r1  |  r1  |      |    |    |    |
        # +------------+------+------+------+----+----+----+

        # ARRANGE
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r1.flush()
        r2.flush()
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
        # TEST CASE
        # Swap room1 with room2 should raise an error
        # because room1 has no reservation between
        # checkin & checkout provided

        # Initial state
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |      |      |      |    |    |    |
        # | Double 102 |  r1  |  r1  |  r1  |    |    |    |
        # +------------+------+------+------+----+----+----+

        # State after swap
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |  r1  |  r1  |  r1  |    |    |    |
        # | Double 102 |      |      |      |    |    |    |
        # +------------+------+------+------+----+----+----+

        # ARRANGE
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
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
        # TEST CASE

        # Initial state
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |  r0  |      |  r1  |    |    |    |
        # | Double 102 |  r2  |  r2  |  r2  |    |    |    |
        # +------------+------+------+------+----+----+----+

        # State after swap
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |  r2  |      |  r2  |    |    |    |
        # | Double 102 |  r0  |  r2  |  r1  |    |    |    |
        # +------------+------+------+------+----+----+----+

        # ARRANGE
        self.create_common_scenario()
        r0 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=2),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r1.flush()
        r2.flush()
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
            and r2.reservation_line_ids[0].room_id == self.room1
            and r2.reservation_line_ids[2].room_id == self.room1
            and r2.reservation_line_ids[1].room_id == self.room2
        )

    def test_swap_reservation_rooms_gap_02(self):
        # TEST CASE

        # Initial state
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |  r0  |      |  r1  |    |    |    |
        # | Double 102 |  r2  |  r2  |  r2  |    |    |    |
        # +------------+------+------+------+----+----+----+

        # State after swap
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |  r2  |  r2  |  r2  |    |    |    |
        # | Double 102 |  r0  |      |  r1  |    |    |    |
        # +------------+------+------+------+----+----+----+

        # ARRANGE
        self.create_common_scenario()
        r0 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )

        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=2),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r2 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r1.flush()
        r2.flush()
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
        # TEST CASE
        # Swap room1 with room2 should raise an error
        # because room1 has no reservation between
        # checkin & checkout provided

        # Initial state
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |      |      |      |    |    |    |
        # | Double 102 |  r1  |  r1  |  r1  |    |    |    |
        # +------------+------+------+------+----+----+----+

        # ARRANGE
        self.create_common_scenario()
        self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
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
        # TEST CASE
        # A reservation is created with preferred room
        # The room for 1st night is switched to another room
        # Expected result:
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |      |  r1  |  r1  |    |    |    |
        # | Double 102 |  r1  |      |      |    |    |    |
        # +------------+------+------+------+----+----+----+

        # ARRANGE
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r1.flush()
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
        # TEST CASE
        # A reservation is created with preferred room
        # The room for 1st night is switched to another room
        # Expected result:
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |  r1  |  r1  |      |    |    |    |
        # | Double 102 |      |      |  r1  |    |    |    |
        # +------------+------+------+------+----+----+----+

        # ARRANGE
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r1.flush()
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
        # TEST CASE
        # A reservation is created with preferred room
        # The room for 1st night is switched to another room
        # Expected result:
        # +------------+------+------+------+----+----+----+
        # | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        # +------------+------+------+------+----+----+----+
        # | Double 101 |  r1  |      |  r1  |    |    |    |
        # | Double 102 |      |  r1  |      |    |    |    |
        # +------------+------+------+------+----+----+----+

        # ARRANGE
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r1.flush()
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
        # TEST CASE
        # Try to split the reservation for one night
        # and set with a non valid room

        # ARRANGE
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r1.flush()
        room_not_exist = self.room3 = self.env["pms.room"].create(
            {
                "pms_property_id": self.test_property.id,
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
        # Try to split the reservation for one night
        # and that night doesn't belong to reservation

        # ARRANGE
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r1.flush()
        # ACT & ASSERT
        with self.assertRaises(UserError):
            self.env["pms.reservation.split.join.swap.wizard"].reservation_split(
                r1, datetime.datetime.now() + datetime.timedelta(days=100), self.room2
            )

    def test_split_reservation_check_room_splitted_not_valid_03(self):
        # TEST CASE
        # Try to split the reservation for one night
        # and the reservation not exists

        # ARRANGE
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r1.flush()
        # ACT & ASSERT
        with self.assertRaises(UserError):
            self.env["pms.reservation.split.join.swap.wizard"].reservation_split(
                self.env["pms.reservation"], datetime.datetime.now(), self.room2
            )

    def test_split_reservation_check_room_splitted_not_valid_04(self):
        # TEST CASE
        # Try to split the reservation to one room
        # and the room is not available

        # ARRANGE
        self.create_common_scenario()
        self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room2.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "preferred_room_id": self.room1.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r1.flush()
        # ACT & ASSERT
        with self.assertRaises(UserError):
            self.env["pms.reservation.split.join.swap.wizard"].reservation_split(
                r1, datetime.datetime.now(), self.room2
            )
