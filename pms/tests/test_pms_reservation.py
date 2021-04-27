import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import common


@freeze_time("2012-01-14")
class TestPmsReservations(common.SavepointCase):
    def create_common_scenario(self):

        self.test_pricelist1 = self.env["product.pricelist"].create(
            {
                "name": "test pricelist 1",
            }
        )
        # create a room type availability
        self.room_type_availability = self.env["pms.availability.plan"].create(
            {
                "name": "Availability plan for TEST",
                "pms_pricelist_ids": [(6, 0, [self.test_pricelist1.id])],
            }
        )

        # create a sequences
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
        # create a property
        self.property = self.env["pms.property"].create(
            {
                "name": "MY PMS TEST",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.test_pricelist1.id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )

        # create room type class
        self.room_type_class = self.env["pms.room.type.class"].create(
            {"name": "Room", "default_code": "ROOM"}
        )

        # create room type
        self.room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.property.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
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

    def create_multiproperty_scenario(self):
        self.create_common_scenario()
        self.property1 = self.env["pms.property"].create(
            {
                "name": "Property_1",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )

        self.property2 = self.env["pms.property"].create(
            {
                "name": "Property_2",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )

        self.property3 = self.env["pms.property"].create(
            {
                "name": "Property_3",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )
        self.room_type_class = self.env["pms.room.type.class"].create(
            {"name": "Room Class", "default_code": "RCTEST"}
        )

        self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Board Service Test",
                "default_code": "CB",
            }
        )

    @freeze_time("1980-11-01")
    def test_create_reservation_start_date(self):
        # TEST CASE
        # reservation should start on checkin day

        # ARRANGE
        self.create_common_scenario()
        today = fields.date.today()
        checkin = today + datetime.timedelta(days=8)
        checkout = checkin + datetime.timedelta(days=11)
        customer = self.env.ref("base.res_partner_12")
        reservation_vals = {
            "checkin": checkin,
            "checkout": checkout,
            "room_type_id": self.room_type_double.id,
            "partner_id": customer.id,
            "pms_property_id": self.property.id,
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
        self.create_common_scenario()
        # ARRANGE
        today = fields.date.today()
        checkin = today + datetime.timedelta(days=8)
        checkout = checkin + datetime.timedelta(days=11)
        customer = self.env.ref("base.res_partner_12")
        reservation_vals = {
            "checkin": checkin,
            "checkout": checkout,
            "room_type_id": self.room_type_double.id,
            "partner_id": customer.id,
            "pms_property_id": self.property.id,
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
                "partner_id": self.env.ref("base.res_partner_12").id,
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
                "partner_id": self.env.ref("base.res_partner_12").id,
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
                "partner_id": self.env.ref("base.res_partner_12").id,
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
                "partner_id": self.env.ref("base.res_partner_12").id,
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
                "partner_id": self.env.ref("base.res_partner_12").id,
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
                "partner_id": self.env.ref("base.res_partner_12").id,
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
                "partner_id": self.env.ref("base.res_partner_12").id,
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
                "partner_id": self.env.ref("base.res_partner_12").id,
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
                "partner_id": self.env.ref("base.res_partner_12").id,
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
                "partner_id": self.env.ref("base.res_partner_12").id,
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
                "partner_id": self.env.ref("base.res_partner_12").id,
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
                "partner_id": self.env.ref("base.res_partner_12").id,
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
                "partner_id": self.env.ref("base.res_partner_12").id,
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
                "partner_id": self.env.ref("base.res_partner_12").id,
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
                    "partner_id": self.env.ref("base.res_partner_12").id,
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
                "partner_id": self.env.ref("base.res_partner_12").id,
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
                    "partner_id": self.env.ref("base.res_partner_12").id,
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
                "partner_id": self.env.ref("base.res_partner_12").id,
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
                "partner_id": self.env.ref("base.res_partner_12").id,
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
                "partner_id": self.env.ref("base.res_partner_12").id,
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
                    "partner_id": self.env.ref("base.res_partner_12").id,
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
                    "partner_id": self.env.ref("base.res_partner_12").id,
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
    def test_order_priority_allowed_checkin(self):
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
        r1.allowed_checkin = False
        # ACT
        reservations = self.env["pms.reservation"].search(
            [("pms_property_id", "=", self.property.id)]
        )
        # ASSERT
        self.assertEqual(r1, reservations[0])

    @freeze_time("1981-11-01")
    def test_order_priority_allowed_checkout(self):
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
        r1.allowed_checkout = True
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
        self.create_multiproperty_scenario()
        host = self.env["res.partner"].create(
            {
                "name": "Miguel",
                "phone": "654667733",
                "email": "miguel@example.com",
            }
        )
        self.reservation_test = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "pms_property_id": self.property1.id,
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
                "class_id": self.room_type_class.id,
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

    @freeze_time("1950-11-01")
    def _test_check_date_order(self):
        self.create_common_scenario()
        customer = self.env.ref("base.res_partner_12")
        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=3),
                "partner_id": customer.id,
            }
        )

        reservation.flush()
        self.assertEqual(
            str(reservation.date_order),
            str(fields.date.today()),
            "Date Order isn't correct",
        )

    def _test_check_checkin_datetime(self):
        self.create_common_scenario()
        customer = self.env.ref("base.res_partner_12")
        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": fields.date.today() + datetime.timedelta(days=300),
                "checkout": fields.date.today() + datetime.timedelta(days=305),
                "partner_id": customer.id,
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
        self.create_common_scenario()
        customer = self.env.ref("base.res_partner_12")
        availability_rule = self.env["pms.availability.plan.rule"].create(
            {
                "pms_property_id": self.property.id,
                "room_type_id": self.room_type_double.id,
                "availability_plan_id": self.room_type_availability.id,
                "date": fields.date.today() + datetime.timedelta(days=153),
            }
        )
        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": fields.date.today() + datetime.timedelta(days=150),
                "checkout": fields.date.today() + datetime.timedelta(days=152),
                "partner_id": customer.id,
                "room_type_id": self.room_type_double.id,
                "pricelist_id": self.test_pricelist1.id,
            }
        )
        self.assertEqual(
            reservation.allowed_room_ids,
            availability_rule.room_type_id.room_ids,
            "Rooms allowed don't match",
        )

    def _test_partner_is_agency(self):
        self.create_common_scenario()
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
                "pms_property_id": self.property.id,
                "checkin": fields.date.today() + datetime.timedelta(days=150),
                "checkout": fields.date.today() + datetime.timedelta(days=152),
                # "partner_id": False,
                "agency_id": agency.id,
                # "folio_id":False,
            }
        )

        reservation.flush()

        self.assertEqual(
            reservation.partner_id.id,
            agency.id,
            "Partner_id doesn't match with agency_id",
        )

    def test_agency_pricelist(self):
        self.create_common_scenario()
        sale_channel1 = self.env["pms.sale.channel"].create(
            {
                "name": "Test Indirect",
                "channel_type": "indirect",
                "product_pricelist_ids": [(6, 0, [self.test_pricelist1.id])],
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
                "pms_property_id": self.property.id,
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
        self.create_common_scenario()
        customer = self.env.ref("base.res_partner_12")
        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": fields.date.today() + datetime.timedelta(days=150),
                "checkout": fields.date.today() + datetime.timedelta(days=152),
                "partner_id": customer.id,
            }
        )

        url = "/my/reservations/%s" % reservation.id
        self.assertEqual(reservation.access_url, url, "Reservation url isn't correct")

    def test_compute_ready_for_checkin(self):
        self.create_common_scenario()
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Miguel",
                "phone": "654667733",
                "email": "miguel@example.com",
            }
        )
        self.host2 = self.env["res.partner"].create(
            {
                "name": "Brais",
                "phone": "654437733",
                "email": "brais@example.com",
            }
        )
        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": "2012-01-14",
                "checkout": "2012-01-17",
                "partner_id": self.host1.id,
                "allowed_checkin": True,
                "pms_property_id": self.property.id,
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

    def test_check_checkin_less_checkout(self):
        self.create_common_scenario()
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Host1",
            }
        )
        with self.assertRaises(ValidationError):
            self.env["pms.reservation"].create(
                {
                    "checkin": fields.date.today() + datetime.timedelta(days=3),
                    "checkout": fields.date.today(),
                    "pms_property_id": self.property.id,
                    "partner_id": self.host1.id,
                }
            )

    def test_check_adults(self):
        self.create_common_scenario()
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Host1",
            }
        )
        with self.assertRaises(ValidationError):
            self.env["pms.reservation"].create(
                {
                    "checkin": fields.date.today() + datetime.timedelta(days=3),
                    "checkout": fields.date.today(),
                    "pms_property_id": self.property.id,
                    "partner_id": self.host1.id,
                    "room_type_id": self.room_type_double.id,
                    "adults": 4,
                }
            )

    def test_check_arrival_hour(self):
        self.create_common_scenario()
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
                    "pms_property_id": self.property.id,
                    "partner_id": self.host1.id,
                    "arrival_hour": "14:00:00",
                }
            )

    def test_check_departure_hour(self):
        self.create_common_scenario()
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
                    "pms_property_id": self.property.id,
                    "partner_id": self.host1.id,
                    "departure_hour": "14:00:00",
                }
            )

    def test_check_property_integrity_room(self):
        self.create_common_scenario()
        self.property2 = self.env["pms.property"].create(
            {
                "name": "MY PMS TEST",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.test_pricelist1.id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Host1",
            }
        )
        self.room_type_double.pms_property_ids = [
            (6, 0, [self.property.id, self.property2.id])
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
        self.create_common_scenario()
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Host1",
            }
        )
        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today() + datetime.timedelta(days=60),
                "checkout": fields.date.today() + datetime.timedelta(days=65),
                "pms_property_id": self.property.id,
                "partner_id": self.host1.id,
            }
        )
        self.reservation2 = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today() + datetime.timedelta(days=60),
                "checkout": fields.date.today() + datetime.timedelta(days=64),
                "pms_property_id": self.property.id,
                "partner_id": self.host1.id,
                "folio_id": self.reservation.folio_id.id,
            }
        )
        self.assertTrue(
            self.reservation.shared_folio,
            "Folio.reservations > 1, so reservation.shared_folio must be True",
        )

    def test_shared_folio_false(self):
        self.create_common_scenario()
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Host1",
            }
        )
        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today() + datetime.timedelta(days=60),
                "checkout": fields.date.today() + datetime.timedelta(days=65),
                "pms_property_id": self.property.id,
                "partner_id": self.host1.id,
            }
        )
        self.assertFalse(
            self.reservation.shared_folio,
            "Folio.reservations = 1, so reservation.shared_folio must be False",
        )

    @freeze_time("1982-11-01")
    def test_reservation_action_cancel_fail(self):
        self.create_common_scenario()
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
                "pms_property_id": self.property.id,
            }
        )

        reservation.state = "cancelled"

        with self.assertRaises(UserError):
            reservation.action_cancel()

    @freeze_time("1983-11-01")
    def test_cancelation_reason_noshow(self):
        self.create_common_scenario()
        Pricelist = self.env["product.pricelist"]
        self.cancelation_rule = self.env["pms.cancelation.rule"].create(
            {
                "name": "Cancelation Rule Test",
                "pms_property_ids": [self.property.id],
                "penalty_noshow": 50,
            }
        )

        self.pricelist = Pricelist.create(
            {
                "name": "Pricelist Test",
                "pms_property_ids": [self.property.id],
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
                "pms_property_id": self.property.id,
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

    @freeze_time("1984-11-01")
    def test_cancelation_reason_intime(self):
        self.create_common_scenario()
        Pricelist = self.env["product.pricelist"]
        self.cancelation_rule = self.env["pms.cancelation.rule"].create(
            {
                "name": "Cancelation Rule Test",
                "pms_property_ids": [self.property.id],
                "days_intime": 3,
            }
        )

        self.pricelist = Pricelist.create(
            {
                "name": "Pricelist Test",
                "pms_property_ids": [self.property.id],
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
                "pms_property_id": self.property.id,
                "pricelist_id": self.pricelist.id,
            }
        )

        reservation.action_cancel()
        reservation.flush()

        self.assertEqual(reservation.cancelled_reason, "intime", "-----------")

    @freeze_time("1985-11-01")
    def _test_cancelation_reason_late(self):
        self.create_common_scenario()
        Pricelist = self.env["product.pricelist"]
        self.cancelation_rule = self.env["pms.cancelation.rule"].create(
            {
                "name": "Cancelation Rule Test",
                "pms_property_ids": [self.property.id],
                "days_late": 3,
            }
        )

        self.pricelist = Pricelist.create(
            {
                "name": "Pricelist Test",
                "pms_property_ids": [self.property.id],
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
                "pms_property_id": self.property.id,
                "pricelist_id": self.pricelist.id,
            }
        )
        reservation.action_cancel()
        reservation.flush()
        self.assertEqual(reservation.cancelled_reason, "late", "-----------")

    def test_compute_checkin_partner_count(self):
        self.create_common_scenario()
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Miguel",
                "phone": "654667733",
                "email": "miguel@example.com",
            }
        )
        self.host2 = self.env["res.partner"].create(
            {
                "name": "Brais",
                "phone": "654437733",
                "email": "brais@example.com",
            }
        )
        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": "2013-01-14",
                "checkout": "2013-01-17",
                "partner_id": self.host1.id,
                "pms_property_id": self.property.id,
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
        self.create_common_scenario()
        self.host1 = self.env["res.partner"].create(
            {
                "name": "Miguel",
                "phone": "654667733",
                "email": "miguel@example.com",
            }
        )
        self.host2 = self.env["res.partner"].create(
            {
                "name": "Brais",
                "phone": "654437733",
                "email": "brais@example.com",
            }
        )
        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": "2014-01-14",
                "checkout": "2014-01-17",
                "partner_id": self.host1.id,
                "pms_property_id": self.property.id,
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

    @freeze_time("1982-11-01")
    def test_reservation_action_checkout_fail(self):
        self.create_common_scenario()
        host = self.env["res.partner"].create(
            {
                "name": "Miguel",
                "phone": "654667733",
                "email": "miguel@example.com",
            }
        )
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "partner_id": host.id,
                "allowed_checkout": True,
                "pms_property_id": self.property.id,
            }
        )

        with self.assertRaises(UserError):
            reservation.action_reservation_checkout()
