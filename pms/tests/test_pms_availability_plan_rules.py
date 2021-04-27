import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import common


@freeze_time("1980-01-01")
class TestPmsRoomTypeAvailabilityRules(common.SavepointCase):
    def create_common_scenario(self):
        self.test_pricelist2 = self.env["product.pricelist"].create(
            {
                "name": "test pricelist 2",
            }
        )
        self.test_property1 = self.env["pms.property"].create(
            {
                "name": "Property 1",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.test_pricelist2.id,
            }
        )
        self.test_property2 = self.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.test_pricelist2.id,
            }
        )
        self.test_pricelist1 = self.env["product.pricelist"].create(
            {
                "name": "test pricelist 1",
                "pms_property_ids": [
                    (4, self.test_property1.id),
                    (4, self.test_property2.id),
                ],
            }
        )

        # pms.availability.plan
        self.test_room_type_availability1 = self.env["pms.availability.plan"].create(
            {
                "name": "Availability plan for TEST",
                "pms_pricelist_ids": [(6, 0, [self.test_pricelist1.id])],
            }
        )
        # SEQUENCES
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
                "default_pricelist_id": self.test_pricelist1.id,
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
                "pms_property_ids": [
                    (4, self.test_property.id),
                ],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.test_room_type_class.id,
            }
        )
        # pms.room
        self.test_room1_double = self.env["pms.room"].create(
            {
                "pms_property_id": self.test_property.id,
                "name": "Double 201 test",
                "room_type_id": self.test_room_type_double.id,
                "capacity": 2,
            }
        )
        # pms.room
        self.test_room2_double = self.env["pms.room"].create(
            {
                "pms_property_id": self.test_property.id,
                "name": "Double 202 test",
                "room_type_id": self.test_room_type_double.id,
                "capacity": 2,
            }
        )
        # pms.room
        # self.test_room3_double = self.env["pms.room"].create(
        #     {
        #         "pms_property_id": self.test_property.id,
        #         "name": "Double 203 test",
        #         "room_type_id": self.test_room_type_double.id,
        #         "capacity": 2,
        #     }
        # )
        # # pms.room
        # self.test_room4_double = self.env["pms.room"].create(
        #     {
        #         "pms_property_id": self.test_property.id,
        #         "name": "Double 204 test",
        #         "room_type_id": self.test_room_type_double.id,
        #         "capacity": 2,
        #     }
        # )
        # pms.room
        self.test_room1_single = self.env["pms.room"].create(
            {
                "pms_property_id": self.test_property.id,
                "name": "Single 101 test",
                "room_type_id": self.test_room_type_single.id,
                "capacity": 1,
            }
        )
        # pms.room
        self.test_room2_single = self.env["pms.room"].create(
            {
                "pms_property_id": self.test_property.id,
                "name": "Single 102 test",
                "room_type_id": self.test_room_type_single.id,
                "capacity": 1,
            }
        )
        # partner
        self.partner1 = self.env["res.partner"].create({"name": "Charles"})

    def create_scenario_multiproperty(self):
        self.create_common_scenario()
        self.test_property3 = self.env["pms.property"].create(
            {
                "name": "Property 3",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.test_pricelist2.id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )
        self.availability_multiproperty = self.env["pms.availability.plan"].create(
            {
                "name": "Availability plan for TEST",
                "pms_pricelist_ids": [(6, 0, [self.test_pricelist1.id])],
                "pms_property_ids": [
                    (4, self.test_property1.id),
                    (4, self.test_property2.id),
                ],
            }
        )

    def test_availability_rooms_all(self):
        # TEST CASE
        # get availability withouth rules

        # ARRANGE
        self.create_common_scenario()

        checkin = fields.date.today()
        checkout = (fields.datetime.today() + datetime.timedelta(days=4)).date()
        test_rooms_double_rooms = self.env["pms.room"].search(
            [("pms_property_id", "=", self.test_property.id)]
        )

        # ACT
        result = self.env["pms.availability.plan"].rooms_available(
            checkin=checkin,
            checkout=checkout,
        )
        # ASSERT
        obtained = all(elem.id in result.ids for elem in test_rooms_double_rooms)
        self.assertTrue(
            obtained,
            "Availability should contain the test rooms"
            "because there's no availability rules for them.",
        )

    def test_availability_rooms_all_lines(self):
        # TEST CASE
        # get availability withouth rules
        # given reservation lines to not consider

        # ARRANGE
        self.create_common_scenario()
        checkin = fields.date.today()
        checkout = (fields.datetime.today() + datetime.timedelta(days=4)).date()
        test_rooms_double_rooms = self.env["pms.room"].search(
            [("pms_property_id", "=", self.test_property.id)]
        )
        test_reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": checkin,
                "checkout": checkout,
                "partner_id": self.partner1.id,
            }
        )

        # ACT
        result = self.env["pms.availability.plan"].rooms_available(
            checkin=checkin,
            checkout=checkout,
            current_lines=test_reservation.reservation_line_ids.ids,
        )
        # ASSERT
        obtained = all(elem.id in result.ids for elem in test_rooms_double_rooms)
        self.assertTrue(
            obtained,
            "Availability should contain the test rooms"
            "because there's no availability rules for them.",
        )

    def test_availability_rooms_room_type(self):
        # TEST CASE
        # get availability withouth rules
        # given a room type

        # ARRANGE
        self.create_common_scenario()
        test_rooms_double_rooms = self.env["pms.room"].search(
            [
                ("pms_property_id", "=", self.test_property.id),
                ("room_type_id", "=", self.test_room_type_double.id),
            ]
        )

        # ACT
        result = self.env["pms.availability.plan"].rooms_available(
            checkin=fields.date.today(),
            checkout=(fields.datetime.today() + datetime.timedelta(days=4)).date(),
            room_type_id=self.test_room_type_double.id,
        )

        # ASSERT
        obtained = all(elem.id in result.ids for elem in test_rooms_double_rooms)
        self.assertTrue(
            obtained,
            "Availability should contain the test rooms"
            "because there's no  availability rules for them.",
        )

    def test_availability_closed_no_room_type(self):
        # TEST CASE:
        # coverage for 2 points:
        # 1. without room type, availability rules associated
        #                      with the pricelist are applied
        # 2. availability rule "closed" is taken into account

        # ARRANGE
        self.create_common_scenario()
        self.test_room_type_availability_rule1 = self.env[
            "pms.availability.plan.rule"
        ].create(
            {
                "availability_plan_id": self.test_room_type_availability1.id,
                "room_type_id": self.test_room_type_double.id,
                "date": (fields.datetime.today() + datetime.timedelta(days=2)).date(),
                "closed": True,  # <- (1/2)
                "pms_property_id": self.test_property.id,
            }
        )
        # ACT
        result = self.env["pms.availability.plan"].rooms_available(
            checkin=fields.date.today(),
            checkout=(fields.datetime.today() + datetime.timedelta(days=4)).date(),
            # room_type_id=False, # <-  (2/2)
            pricelist_id=self.test_pricelist1.id,
        )
        # ASSERT
        self.assertNotIn(
            self.test_room_type_double,
            result.mapped("room_type_id"),
            "Availability should not contain rooms of a type "
            "which its availability rules applies",
        )

    def test_availability_rules(self):
        # TEST CASE
        # the availability should take into acount availability rules:
        # closed_arrival, closed_departure, min_stay, max_stay,
        # min_stay_arrival, max_stay_arrival

        # ARRANGE
        self.create_common_scenario()

        self.test_room_type_availability_rule1 = self.env[
            "pms.availability.plan.rule"
        ].create(
            {
                "availability_plan_id": self.test_room_type_availability1.id,
                "room_type_id": self.test_room_type_double.id,
                "date": (fields.datetime.today() + datetime.timedelta(days=0)).date(),
                "pms_property_id": self.test_property.id,
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
                "quota": -1,
                "max_avail": -1,
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
                "quota": -1,
                "max_avail": -1,
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
                "quota": -1,
                "max_avail": -1,
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
                "quota": -1,
                "max_avail": -1,
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
                "quota": -1,
                "max_avail": -1,
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
                "quota": -1,
                "max_avail": -1,
                "date": checkin,
            },
            {
                "closed": False,
                "closed_arrival": False,
                "closed_departure": False,
                "min_stay": 0,
                "max_stay": 0,
                "min_stay_arrival": 0,
                "max_stay_arrival": 0,
                "quota": 0,
                "max_avail": -1,
                "date": checkin,
            },
            {
                "closed": False,
                "closed_arrival": False,
                "closed_departure": False,
                "min_stay": 0,
                "max_stay": 0,
                "min_stay_arrival": 0,
                "max_stay_arrival": 0,
                "quota": -1,
                "max_avail": 0,
                "date": checkin,
            },
        ]

        for test_case in test_cases:
            with self.subTest(k=test_case):

                # ACT
                self.test_room_type_availability_rule1.write(test_case)

                result = self.env["pms.availability.plan"].rooms_available(
                    checkin=checkin,
                    checkout=checkout,
                    room_type_id=self.test_room_type_double.id,
                    pricelist_id=self.test_pricelist1.id,
                )

                # ASSERT
                self.assertNotIn(
                    self.test_room_type_double,
                    result.mapped("room_type_id"),
                    "Availability should not contain rooms of a type "
                    "which its availability rules applies",
                )

    @freeze_time("1980-11-01")
    def test_rule_on_create_reservation(self):
        # TEST CASE
        # an availability rule should be applied that would prevent the
        # creation of reservations

        # ARRANGE
        self.create_common_scenario()
        self.test_room_type_availability_rule1 = self.env[
            "pms.availability.plan.rule"
        ].create(
            {
                "availability_plan_id": self.test_room_type_availability1.id,
                "room_type_id": self.test_room_type_double.id,
                "date": (fields.datetime.today() + datetime.timedelta(days=2)).date(),
                "closed": True,
                "pms_property_id": self.test_property.id,
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
                    "pms_property_id": self.test_property.id,
                    "checkin": checkin,
                    "checkout": checkout,
                    "adults": 2,
                    "room_type_id": self.test_room_type_double.id,
                    "pricelist_id": self.test_pricelist1.id,
                    "partner_id": self.partner1.id,
                }
            )

    @freeze_time("1980-11-01")
    def test_rules_on_create_splitted_reservation(self):
        # TEST CASE
        # an availability rule should be applied that would prevent the
        # creation of reservations including splitted reservations.

        # ARRANGE
        self.create_common_scenario()
        self.test_room_type_availability_rule1 = self.env[
            "pms.availability.plan.rule"
        ].create(
            {
                "availability_plan_id": self.test_room_type_availability1.id,
                "room_type_id": self.test_room_type_double.id,
                "date": (fields.datetime.today() + datetime.timedelta(days=2)).date(),
                "closed": True,
                "pms_property_id": self.test_property.id,
            }
        )

        checkin_test = datetime.datetime.now()
        checkout_test = datetime.datetime.now() + datetime.timedelta(days=4)

        self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "room_type_id": self.test_room_type_double.id,
                "preferred_room_id": self.test_room1_double.id,
                "partner_id": self.partner1.id,
            }
        )

        self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=2),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=4),
                "adults": 2,
                "room_type_id": self.test_room_type_double.id,
                "preferred_room_id": self.test_room2_double.id,
                "partner_id": self.partner1.id,
            }
        )

        # ACT & ASSERT
        with self.assertRaises(
            ValidationError,
            msg="Availability rule should be applied that would"
            " prevent the creation of splitted reservation.",
        ):
            self.env["pms.reservation"].create(
                {
                    "pms_property_id": self.test_property.id,
                    "checkin": checkin_test,
                    "checkout": checkout_test,
                    "adults": 2,
                    "room_type_id": self.test_room_type_double.id,
                    "pricelist_id": self.test_pricelist1.id,
                    "partner_id": self.partner1.id,
                }
            )

    @freeze_time("1980-11-01")
    def test_rule_update_quota_on_create_reservation(self):
        # TEST CASE
        # quota rule is changed after creating a reservation
        # with pricelist linked to a availability plan that applies

        # ARRANGE
        self.create_common_scenario()

        self.test_room_type_availability_rule1 = self.env[
            "pms.availability.plan.rule"
        ].create(
            {
                "availability_plan_id": self.test_room_type_availability1.id,
                "room_type_id": self.test_room_type_double.id,
                "date": datetime.date.today(),
                "quota": 1,
                "pms_property_id": self.test_property.id,
            }
        )
        self.test_pricelist1.pms_property_ids = [
            (4, self.test_property1.id),
            (4, self.test_property2.id),
            (4, self.test_property.id),
        ]
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.date.today(),
                "checkout": datetime.date.today() + datetime.timedelta(days=1),
                "adults": 2,
                "room_type_id": self.test_room_type_double.id,
                "pricelist_id": self.test_pricelist1.id,
                "partner_id": self.partner1.id,
            }
        )
        r1.flush()
        with self.assertRaises(
            ValidationError,
            msg="The quota shouldnt be enough to create a new reservation",
        ):
            self.env["pms.reservation"].create(
                {
                    "pms_property_id": self.test_property.id,
                    "checkin": datetime.date.today(),
                    "checkout": datetime.date.today() + datetime.timedelta(days=1),
                    "adults": 2,
                    "room_type_id": self.test_room_type_double.id,
                    "pricelist_id": self.test_pricelist1.id,
                    "partner_id": self.partner1.id,
                }
            )

    @freeze_time("1980-11-01")
    def test_rule_update_quota_on_update_reservation(self):
        # TEST CASE
        # quota rule is restored after creating a reservation
        # with pricelist linked to a availability rule that applies
        # and then modify the pricelist of the reservation and
        # no rules applies

        # ARRANGE
        self.create_common_scenario()
        test_quota = 2
        test_pricelist2 = self.env["product.pricelist"].create(
            {
                "name": "test pricelist 2",
            }
        )
        self.test_pricelist1.pms_property_ids = [
            (4, self.test_property1.id),
            (4, self.test_property2.id),
            (4, self.test_property.id),
        ]
        rule = self.env["pms.availability.plan.rule"].create(
            {
                "availability_plan_id": self.test_room_type_availability1.id,
                "room_type_id": self.test_room_type_double.id,
                "date": datetime.date.today(),
                "quota": test_quota,
                "pms_property_id": self.test_property.id,
            }
        )
        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.date.today(),
                "checkout": datetime.date.today() + datetime.timedelta(days=1),
                "adults": 2,
                "room_type_id": self.test_room_type_double.id,
                "pricelist_id": self.test_pricelist1.id,
                "partner_id": self.partner1.id,
            }
        )

        # ACT
        reservation.pricelist_id = test_pricelist2.id
        reservation.flush()
        self.assertEqual(
            test_quota,
            rule.quota,
            "The quota should be restored after changing the reservation's pricelist",
        )

    def test_availability_closed_no_room_type_check_property(self):
        # TEST CASE:
        # check that availability rules are applied to the correct properties
        # There are two properties:
        # test_property   --> test_room_type_availability_rule1
        # test_property2  --> test_room_type_availability_rule2

        # ARRANGE
        self.create_scenario_multiproperty()
        self.test_room_type_special = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [
                    (4, self.test_property1.id),
                    (4, self.test_property2.id),
                ],
                "name": "Special Room Test",
                "default_code": "SP_Test",
                "class_id": self.test_room_type_class.id,
            }
        )
        self.test_room1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.test_property1.id,
                "name": "Double 201 test",
                "room_type_id": self.test_room_type_special.id,
                "capacity": 2,
            }
        )
        # pms.room
        self.test_room2 = self.env["pms.room"].create(
            {
                "pms_property_id": self.test_property2.id,
                "name": "Double 202 test",
                "room_type_id": self.test_room_type_special.id,
                "capacity": 2,
            }
        )
        self.test_room_type_availability_rule1 = self.env[
            "pms.availability.plan.rule"
        ].create(
            {
                "availability_plan_id": self.availability_multiproperty.id,
                "room_type_id": self.test_room_type_special.id,
                "date": (fields.datetime.today() + datetime.timedelta(days=2)).date(),
                "closed": True,
                "pms_property_id": self.test_property1.id,
            }
        )
        self.test_room_type_availability_rule2 = self.env[
            "pms.availability.plan.rule"
        ].create(
            {
                "availability_plan_id": self.availability_multiproperty.id,
                "room_type_id": self.test_room_type_special.id,
                "date": (fields.datetime.today() + datetime.timedelta(days=2)).date(),
                "pms_property_id": self.test_property2.id,
            }
        )

        # check that for that date test_property1 doesnt have rooms available
        # (of that type:test_room_type_double),
        # instead, property2 has test_room_type_double available
        properties = [
            {"property": self.test_property1.id, "value": False},
            {"property": self.test_property2.id, "value": True},
        ]

        for p in properties:
            with self.subTest(k=p):
                # ACT
                rooms_avail = self.env["pms.availability.plan"].rooms_available(
                    checkin=fields.date.today(),
                    checkout=(
                        fields.datetime.today() + datetime.timedelta(days=2)
                    ).date(),
                    room_type_id=self.test_room_type_special.id,
                    pricelist_id=self.test_pricelist1.id,
                    pms_property_id=p["property"],
                )
                # ASSERT
                self.assertEqual(
                    len(rooms_avail) > 0, p["value"], "Availability is not correct"
                )

    def test_check_property_availability_room_type(self):
        # TEST CASE:
        # check integrity between availability properties and room_type properties

        # ARRANGE
        self.create_scenario_multiproperty()
        # create new room_type
        self.test_room_type_special = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [
                    (4, self.test_property1.id),
                    (4, self.test_property3.id),
                ],
                "name": "Special Room Test",
                "default_code": "SP_Test",
                "class_id": self.test_room_type_class.id,
            }
        )
        # ACT
        self.availability_example = self.env["pms.availability.plan"].create(
            {
                "name": "Availability plan for TEST",
                "pms_pricelist_ids": [(6, 0, [self.test_pricelist1.id])],
                "pms_property_ids": [
                    (4, self.test_property1.id),
                    (4, self.test_property2.id),
                ],
            }
        )
        self.availability_rule1 = self.env["pms.availability.plan.rule"].create(
            {
                "availability_plan_id": self.availability_example.id,
                "room_type_id": self.test_room_type_special.id,
                "date": (fields.datetime.today() + datetime.timedelta(days=2)).date(),
                "closed": True,
                "pms_property_id": self.test_property1.id,
            }
        )
        # Test cases when creating a availability_rule
        # Allowed properties:
        # Room Type(test_room_type_special)      -->TEST_PROPERTY1 TEST_PROPERTY3
        # Availability Plan(availability_example)-->TEST_PROPERTY1 TEST_PROPERTY2

        # Both cases throw an exception:
        # 1:Rule for property2,
        #    it is allowed in availability_plan but not in room_type
        # 2:Rule for property3,
        #    it is allowed in room_type, but not in availability_plan

        test_cases = [
            {
                "pms_property_id": self.test_property2.id,
            },
            {
                "pms_property_id": self.test_property3.id,
            },
        ]
        # ASSERT
        for test_case in test_cases:
            with self.subTest(k=test_case):
                with self.assertRaises(UserError):
                    self.availability_rule1.pms_property_id = test_case[
                        "pms_property_id"
                    ]
