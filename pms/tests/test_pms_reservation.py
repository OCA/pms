import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import ValidationError

from .common import TestHotel


@freeze_time("2012-01-14")
class TestPmsReservations(TestHotel):
    def create_common_scenario(self):
        # create a room type restriction
        self.room_type_restriction = self.env["pms.room.type.restriction"].create(
            {"name": "Restriction plan for TEST"}
        )

        # create a property
        self.property = self.env["pms.property"].create(
            {
                "name": "MY PMS TEST",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "default_restriction_id": self.room_type_restriction.id,
            }
        )

        # create room type class
        self.room_type_class = self.env["pms.room.type.class"].create({"name": "Room"})

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

    def test_create_reservation(self):
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
        reservation = self.env["pms.reservation"].create(reservation_vals)

        self.assertEqual(
            reservation.reservation_line_ids[0].date,
            checkin,
            "Reservation lines don't start in the correct date",
        )
        self.assertEqual(
            reservation.reservation_line_ids[-1].date,
            checkout - datetime.timedelta(1),
            "Reservation lines don't end in the correct date",
        )

    @freeze_time("1980-11-01")
    def test_split_reservation01(self):
        """
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

        self.create_common_scenario()

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
        obtained = all(
            elem.room_id.id == r_test.reservation_line_ids[0].room_id.id
            for elem in r_test.reservation_line_ids
        )
        self.assertTrue(
            obtained, "The entire reservation should be allocated in the preferred room"
        )

    @freeze_time("1980-11-01")
    def test_split_reservation02(self):
        """
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
        self.create_common_scenario()

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
        self.assertFalse(r_test.splitted, "The reservation shouldn't be splitted")

    @freeze_time("1980-11-01")
    def test_split_reservation03(self):
        """
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
        changes = 0
        last_room = None

        for line in r_test.reservation_line_ids:
            if last_room != line.room_id.id:
                last_room = line.room_id.id
                changes += 1

        self.assertEqual(
            2, changes, "The reservation shouldn't have more than 2 changes"
        )

    @freeze_time("1980-11-01")
    def test_split_reservation04(self):
        """
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

        changes = 0
        last_room = None
        for line in r_test.reservation_line_ids:
            if line.room_id != last_room:
                last_room = line.room_id
                changes += 1

        self.assertEqual(
            3, changes, "The reservation shouldn't be splitted in more than 3 roomss"
        )

    @freeze_time("1980-11-01")
    def test_split_reservation05(self):
        """
        The preferred room_id is not available
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |r1/tst|      |      |    |    |    |
        | Double 102 |      |      |      |    |    |    |
        | Double 103 |      |      |      |    |    |    |
        +------------+------+------+------+----+----+----+
        """

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
        There's no availability in the preferred_room_id provided
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r1  |r1/tst|  tst |    |    |    |
        | Double 102 |      |      |      |    |    |    |
        | Double 103 |      |      |      |    |    |    |
        +------------+------+------+------+----+----+----+
        """

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
        There's no availability
        +------------+------+------+------+----+----+----+
        | room/date  |  01  |  02  |  03  | 04 | 05 | 06 |
        +------------+------+------+------+----+----+----+
        | Double 101 |  r1  |  r1  |  r1  |    |    |    |
        | Double 102 |  r2  |  r2  |  r2  |    |    |    |
        | Double 103 |  r3  |  r3  |  r3  |    |    |    |
        +------------+------+------+------+----+----+----+
        """

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

        with self.assertRaises(ValidationError):
            r_test = self.env["pms.reservation"].create(
                {
                    "pms_property_id": self.property.id,
                    "checkin": datetime.datetime.now(),
                    "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                    "adults": 2,
                    "room_type_id": self.room_type_double.id,
                }
            )
            r_test.flush()

    def test_manage_children_raise(self):

        # ARRANGE
        PmsReservation = self.env["pms.reservation"]

        # ACT & ASSERT
        with self.assertRaises(ValidationError), self.cr.savepoint():

            PmsReservation.create(
                {
                    "adults": 2,
                    "children_occupying": 1,
                    "checkin": datetime.datetime.now(),
                    "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                    "room_type_id": self.browse_ref("pms.pms_room_type_0").id,
                }
            )
