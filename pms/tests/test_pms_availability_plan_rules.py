import datetime

from odoo import fields
from odoo.exceptions import ValidationError

from .common import TestPms


class TestPmsRoomTypeAvailabilityRules(TestPms):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pms_property2 = cls.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": cls.company1.id,
                "default_pricelist_id": cls.pricelist1.id,
            }
        )
        cls.pricelist2 = cls.env["product.pricelist"].create(
            {
                "name": "test pricelist 1",
                "pms_property_ids": [
                    (4, cls.pms_property1.id),
                    (4, cls.pms_property2.id),
                ],
                "availability_plan_id": cls.availability_plan1.id,
                "is_pms_available": True,
            }
        )
        # pms.sale.channel
        cls.sale_channel_direct1 = cls.env["pms.sale.channel"].create(
            {
                "name": "Door",
                "channel_type": "direct",
            }
        )
        # pms.availability.plan
        cls.test_room_type_availability1 = cls.env["pms.availability.plan"].create(
            {
                "name": "Availability plan for TEST",
                "pms_pricelist_ids": [(6, 0, [cls.pricelist2.id])],
            }
        )
        # pms.property
        cls.pms_property3 = cls.env["pms.property"].create(
            {
                "name": "MY PMS TEST",
                "company_id": cls.company1.id,
                "default_pricelist_id": cls.pricelist2.id,
            }
        )
        cls.pricelist2.write(
            {
                "pms_property_ids": [
                    (4, cls.pms_property3.id),
                ],
            }
        )

        # pms.room.type
        cls.test_room_type_single = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property3.id],
                "name": "Single Test",
                "default_code": "SNG_Test",
                "class_id": cls.room_type_class1.id,
            }
        )
        # pms.room.type
        cls.test_room_type_double = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [
                    (4, cls.pms_property3.id),
                ],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": cls.room_type_class1.id,
            }
        )
        # pms.room
        cls.test_room1_double = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property3.id,
                "name": "Double 201 test",
                "room_type_id": cls.test_room_type_double.id,
                "capacity": 2,
            }
        )
        # pms.room
        cls.test_room2_double = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property3.id,
                "name": "Double 202 test",
                "room_type_id": cls.test_room_type_double.id,
                "capacity": 2,
            }
        )
        cls.test_room1_single = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property3.id,
                "name": "Single 101 test",
                "room_type_id": cls.test_room_type_single.id,
                "capacity": 1,
            }
        )
        # pms.room
        cls.test_room2_single = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property3.id,
                "name": "Single 102 test",
                "room_type_id": cls.test_room_type_single.id,
                "capacity": 1,
            }
        )
        # partner
        cls.partner1 = cls.env["res.partner"].create(
            {"name": "Charles", "property_product_pricelist": cls.pricelist1}
        )

    def test_availability_rooms_all(self):
        """
        Check the availability of rooms in a property with an availability plan without
        availability rules.
        ---------------------
        The checkin and checkout dates on which the availability will be checked are
        saved in a variable and in another all the rooms of the property are also saved.
        Then the free_room_ids compute field is called which should return the number of
        available rooms of the property and they are saved in another variable with
        which it is verified that all the rooms have been returned because there are no
        availability rules for that plan.
        """

        # ARRANGE
        checkin = fields.date.today()
        checkout = (fields.datetime.today() + datetime.timedelta(days=4)).date()
        test_rooms_double_rooms = self.env["pms.room"].search(
            [("pms_property_id", "=", self.pms_property3.id)]
        )
        # ACT
        pms_property = self.pms_property3.with_context(
            checkin=checkin,
            checkout=checkout,
        )
        result = pms_property.free_room_ids

        # ASSERT
        obtained = all(elem.id in result.ids for elem in test_rooms_double_rooms)
        self.assertTrue(
            obtained,
            "Availability should contain the test rooms"
            "because there's no availability rules for them.",
        )

    def test_availability_rooms_all_lines(self):
        """
        Check the availability of rooms in a property with an availability plan without
        availability rules and passing it the reservation lines of a reservation for
        that property.
        -----------------
        The checkin and checkout dates on which the availability will be checked are
        saved in a variable and in another all the rooms of the property are also saved.
        Then create a reservation for this property and the free_room_ids compute field
        is called with the parameters checkin, checkout and the reservation lines of the
        reservation as a curent lines, this method should return the number of available
        rooms of the property. Then the result is saved in another variable with which
        it is verified that all the rooms have been returned because there are no
        availability rules for that plan.
        """

        # ARRANGE
        checkin = fields.date.today()
        checkout = (fields.datetime.today() + datetime.timedelta(days=4)).date()
        test_rooms_double_rooms = self.env["pms.room"].search(
            [("pms_property_id", "=", self.pms_property3.id)]
        )
        test_reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property3.id,
                "checkin": checkin,
                "checkout": checkout,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ACT
        # REVIEW: reservation without room and wihout room type?
        pms_property = self.pms_property3.with_context(
            checkin=checkin,
            checkout=checkout,
            current_lines=test_reservation.reservation_line_ids.ids,
        )
        result = pms_property.free_room_ids

        # ASSERT
        obtained = all(elem.id in result.ids for elem in test_rooms_double_rooms)
        self.assertTrue(
            obtained,
            "Availability should contain the test rooms"
            "because there's no availability rules for them.",
        )

    def test_availability_rooms_room_type(self):
        """
        Check the availability of a room type for a property.
        ----------------
        Double rooms of a property are saved in a variable. The free_room_ids compute
        field is called giving as parameters checkin, checkout and the type of room
        (in this case double). Then with the all () function we check that all rooms of
        this type were returned.
        """

        # ARRANGE
        test_rooms_double_rooms = self.env["pms.room"].search(
            [
                ("pms_property_id", "=", self.pms_property3.id),
                ("room_type_id", "=", self.test_room_type_double.id),
            ]
        )
        # ACT
        pms_property = self.pms_property3.with_context(
            checkin=fields.date.today(),
            checkout=(fields.datetime.today() + datetime.timedelta(days=4)).date(),
            room_type_id=self.test_room_type_double.id,
        )
        result = pms_property.free_room_ids

        # ASSERT
        obtained = all(elem.id in result.ids for elem in test_rooms_double_rooms)
        self.assertTrue(
            obtained,
            "Availability should contain the test rooms"
            "because there's no  availability rules for them.",
        )

    def test_availability_closed_no_room_type(self):
        """
        Check that rooms of a type with an availability rule with closed = True are
        not available on the dates marked in the date field of the availability rule.
        --------------------
        Create an availability rule for double rooms with the field closed = true
        and the date from today until tomorrow. Then the availability is saved in a
        variable through the free_room_ids computed field, passing it the pricelist that
        it contains the availability plan where the rule is included, and the checkin
        and checkout dates are between the date of the rule. Then it is verified that
        the double rooms are not available.
        """
        # ARRANGE
        self.test_room_type_availability_rule1 = self.env[
            "pms.availability.plan.rule"
        ].create(
            {
                "availability_plan_id": self.test_room_type_availability1.id,
                "room_type_id": self.test_room_type_double.id,
                "date": (fields.datetime.today() + datetime.timedelta(days=2)).date(),
                "closed": True,  # <- (1/2)
                "pms_property_id": self.pms_property3.id,
            }
        )
        # ACT
        pms_property = self.pms_property3.with_context(
            checkin=fields.date.today(),
            checkout=(fields.datetime.today() + datetime.timedelta(days=4)).date(),
            # room_type_id=False, # <-  (2/2)
            pricelist_id=self.pricelist2.id,
        )
        result = pms_property.free_room_ids

        # ASSERT
        self.assertNotIn(
            self.test_room_type_double,
            result.mapped("room_type_id"),
            "Availability should not contain rooms of a type "
            "which its availability rules applies",
        )

    def test_availability_rules(self):
        """
        Check through subtests that the availability rules are applied
        for a specific room type.
        ----------------
        Test cases:
        1. closed_arrival = True
        2. closed_departure = True
        3. min_stay = 5
        4. max_stay = 2
        5. min_stay_arrival = 5
        6. max_stay_arrival = 3
        For each test case, it is verified through the free_room_ids compute field,
        that double rooms are not available since the rules are applied to this
        room type.
        """

        # ARRANGE

        self.test_room_type_availability_rule1 = self.env[
            "pms.availability.plan.rule"
        ].create(
            {
                "availability_plan_id": self.test_room_type_availability1.id,
                "room_type_id": self.test_room_type_double.id,
                "date": fields.date.today(),
                "pms_property_id": self.pms_property3.id,
            }
        )

        checkin = fields.date.today()
        checkout = (fields.datetime.today() + datetime.timedelta(days=4)).date()

        test_cases = [
            {
                "closed": False,
                "closed_arrival": True,
                "closed_departure": False,
                "min_stay": 0,
                "max_stay": 0,
                "min_stay_arrival": 0,
                "max_stay_arrival": 0,
                "date": checkin,
            },
            {
                "closed": False,
                "closed_arrival": False,
                "closed_departure": True,
                "min_stay": 0,
                "max_stay": 0,
                "min_stay_arrival": 0,
                "max_stay_arrival": 0,
                "date": checkout,
            },
            {
                "closed": False,
                "closed_arrival": False,
                "closed_departure": False,
                "min_stay": 5,
                "max_stay": 0,
                "min_stay_arrival": 0,
                "max_stay_arrival": 0,
                "date": checkin,
            },
            {
                "closed": False,
                "closed_arrival": False,
                "closed_departure": False,
                "min_stay": 0,
                "max_stay": 2,
                "min_stay_arrival": 0,
                "max_stay_arrival": 0,
                "date": checkin,
            },
            {
                "closed": False,
                "closed_arrival": False,
                "closed_departure": False,
                "min_stay": 0,
                "max_stay": 0,
                "min_stay_arrival": 5,
                "max_stay_arrival": 0,
                "date": checkin,
            },
            {
                "closed": False,
                "closed_arrival": False,
                "closed_departure": False,
                "min_stay": 0,
                "max_stay": 0,
                "min_stay_arrival": 0,
                "max_stay_arrival": 3,
                "date": checkin,
            },
        ]

        for test_case in test_cases:
            with self.subTest(k=test_case):
                # ACT
                self.test_room_type_availability_rule1.write(test_case)
                # free_room_ids is a non stored compute with depends_context and
                # no field dependency, so writing the rule does not invalidate
                # it and every case would read the value of the first one.
                self.env.invalidate_all()

                pms_property = self.pms_property3.with_context(
                    checkin=checkin,
                    checkout=checkout,
                    room_type_id=self.test_room_type_double.id,
                    pricelist_id=self.pricelist2.id,
                )
                result = pms_property.free_room_ids

                # ASSERT
                self.assertNotIn(
                    self.test_room_type_double,
                    result.mapped("room_type_id"),
                    "Availability should not contain rooms of a type "
                    "which its availability rules applies",
                )

    def test_rule_on_create_reservation(self):
        """
        Check that a reservation is not created when an availability rule prevents it .
        -------------------
        Create an availability rule for double rooms with the
        field closed = True and the date from today until tomorrow. Then try to create
        a reservation for that type of room with a checkin date today and a checkout
        date within 4 days. This should throw a ValidationError since the rule does
        not allow creating reservations for those dates.
        """

        # ARRANGE
        self.test_room_type_availability_rule1 = self.env[
            "pms.availability.plan.rule"
        ].create(
            {
                "availability_plan_id": self.test_room_type_availability1.id,
                "room_type_id": self.test_room_type_double.id,
                "date": (fields.datetime.today() + datetime.timedelta(days=2)).date(),
                "closed": True,
                "pms_property_id": self.pms_property3.id,
            }
        )
        checkin = datetime.datetime.now()
        checkout = datetime.datetime.now() + datetime.timedelta(days=4)

        # ACT & ASSERT
        with self.assertRaises(
            ValidationError,
            msg="Availability rules should be applied that would"
            " prevent the creation of the reservation.",
        ):
            self.env["pms.reservation"].create(
                {
                    "pms_property_id": self.pms_property3.id,
                    "checkin": checkin,
                    "checkout": checkout,
                    "adults": 2,
                    "room_type_id": self.test_room_type_double.id,
                    "pricelist_id": self.pricelist2.id,
                    "partner_id": self.partner1.id,
                }
            )

    def test_room_deactivation_updates_real_avail(self):
        """
        Check that deactivating a room propagates to the availability.
        --------------------------------------------------------------
        Room type with 2 rooms and one reservation for the date: the
        physical availability is 1. Deactivating the remaining free room
        must leave the room type with a single (occupied) active room, so
        real_avail has to be recomputed to 0. That is the value the
        commercial inventory is intersected with, so a stale one oversells
        on the OTAs.
        """
        # ARRANGE
        checkin = fields.date.today() + datetime.timedelta(days=1)
        checkout = checkin + datetime.timedelta(days=1)
        rule = self.env["pms.availability.plan.rule"].create(
            {
                "availability_plan_id": self.test_room_type_availability1.id,
                "room_type_id": self.test_room_type_double.id,
                "date": checkin,
                "pms_property_id": self.pms_property3.id,
            }
        )
        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property3.id,
                "checkin": checkin,
                "checkout": checkout,
                "partner_id": self.partner1.id,
                "room_type_id": self.test_room_type_double.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        self.assertEqual(
            rule.real_avail,
            1,
            "One of the two rooms is occupied, real_avail should be 1",
        )
        free_room = (
            self.test_room1_double + self.test_room2_double
        ) - reservation.reservation_line_ids.room_id

        # ACT
        free_room.active = False

        # ASSERT
        self.assertEqual(
            rule.real_avail,
            0,
            "The only active room of the room type is occupied, so"
            " real_avail should have been recomputed to 0",
        )
