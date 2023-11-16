import datetime

from freezegun import freeze_time

from odoo import fields

from .common import TestPms


class TestPmsBookingEngine(TestPms):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # CREATION OF ROOM TYPE (WITH ROOM TYPE CLASS)
        cls.test_room_type_double = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": cls.room_type_class1.id,
                "list_price": 40.0,
            }
        )

        # pms.room
        cls.test_room1_double = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Double 201 test",
                "room_type_id": cls.test_room_type_double.id,
                "capacity": 2,
            }
        )

        # pms.room
        cls.test_room2_double = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Double 202 test",
                "room_type_id": cls.test_room_type_double.id,
                "capacity": 2,
            }
        )

        # pms.room
        cls.test_room3_double = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Double 203 test",
                "room_type_id": cls.test_room_type_double.id,
                "capacity": 2,
            }
        )

        # pms.room
        cls.test_room4_double = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Double 204 test",
                "room_type_id": cls.test_room_type_double.id,
                "capacity": 2,
            }
        )

        # res.partner
        cls.partner_id = cls.env["res.partner"].create(
            {
                "name": "Miguel",
                "mobile": "654667733",
                "email": "miguel@example.com",
            }
        )

        # pms.sale.channel
        cls.sale_channel_direct1 = cls.env["pms.sale.channel"].create(
            {
                "name": "Door",
                "channel_type": "direct",
            }
        )

    def test_price_wizard_correct(self):
        # TEST CASE
        """
        Check by subtests if the total_price field is applied correctly
        with and without discount.
        ------------
        Create two test cases: one with the discount at 0 and with the
        expected total price, which is the difference in days between
        checkin and checkout, multiplied by the room price and multiplied
        by the number of rooms, and another with the discount at 0.5 and with
        total price the same as the first. Then the wizard is created and it
        is verified that the wizard's total_price_folio is the same as the
        expected price.
        """

        # ARRANGE

        # checkin & checkout
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)
        days = (checkout - checkin).days
        num_double_rooms = 4
        discounts = [
            {
                "discount": 0,
                "expected_price": days
                * self.test_room_type_double.list_price
                * num_double_rooms,
            },
            {
                "discount": 0.5,
                "expected_price": (
                    days * self.test_room_type_double.list_price * num_double_rooms
                )
                * 0.5,
            },
        ]

        # create folio wizard with partner id => pricelist & start-end dates
        booking_engine = self.env["pms.booking.engine"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "channel_type_id": self.sale_channel_direct1.id,
            }
        )

        # force pricelist load

        # availability items belonging to test property
        lines_availability_test = self.env["pms.folio.availability.wizard"].search(
            [
                ("room_type_id.pms_property_ids", "in", self.pms_property1.id),
            ]
        )

        # set value for room type double
        value = self.env["pms.num.rooms.selection"].search(
            [
                ("room_type_id", "=", self.test_room_type_double.id),
                ("value", "=", num_double_rooms),
            ]
        )

        lines_availability_test[0].num_rooms_selected = value
        for discount in discounts:
            with self.subTest(k=discount):
                # ACT
                booking_engine.discount = discount["discount"]

                # ASSERT
                self.assertEqual(
                    booking_engine.total_price_folio,
                    discount["expected_price"],
                    "The total price calculation is wrong",
                )

    def test_price_wizard_correct_pricelist_applied(self):
        """
        Check that the total_price field is applied correctly in
        the wizard(pricelist applied).
        ------------------
        Create a pricelist item for pricelist1 and a wizard is also
        created with pricelist1. Then it is verified that the value
        of the total price of the wizard corresponds to the value of
        the price of the pricelist item.
        """

        # ARRANGE
        # checkin & checkout
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)
        days = (checkout - checkin).days

        # num. rooms of type double to book
        num_double_rooms = 4

        # price for today
        price_today = 38.0

        # expected price
        expected_price_total = days * price_today * num_double_rooms

        # set pricelist item for current day
        product_tmpl = self.test_room_type_double.product_id.product_tmpl_id
        self.env["product.pricelist.item"].create(
            {
                "pricelist_id": self.pricelist1.id,
                "date_start_consumption": checkin,
                "date_end_consumption": checkin,
                "compute_price": "fixed",
                "applied_on": "1_product",
                "product_tmpl_id": product_tmpl.id,
                "fixed_price": price_today,
                "min_quantity": 0,
                "pms_property_ids": product_tmpl.pms_property_ids.ids,
            }
        )

        # create folio wizard with partner id => pricelist & start-end dates
        booking_engine = self.env["pms.booking.engine"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pricelist_id": self.pricelist1.id,
                "pms_property_id": self.pms_property1.id,
                "channel_type_id": self.sale_channel_direct1.id,
            }
        )

        # availability items belonging to test property
        lines_availability_test = self.env["pms.folio.availability.wizard"].search(
            [
                ("room_type_id.pms_property_ids", "in", self.pms_property1.id),
            ]
        )

        # set value for room type double
        value = self.env["pms.num.rooms.selection"].search(
            [
                ("room_type_id", "=", self.test_room_type_double.id),
                ("value", "=", num_double_rooms),
            ]
        )

        # ACT
        lines_availability_test[0].num_rooms_selected = value

        # ASSERT
        self.assertEqual(
            booking_engine.total_price_folio,
            expected_price_total,
            "The total price calculation is wrong",
        )

    # REVIEW: This test is set to check min qty, but the workflow price, actually,
    # always is set to 1 qty and the min_qty cant be applied.
    # We could set qty to number of rooms??

    # def test_price_wizard_correct_pricelist_applied_min_qty_applied(self):
    #     # TEST CASE
    #     # Set values for the wizard and the total price is correct
    #     # (pricelist applied)

    #     # ARRANGE
    #     # common scenario
    #     self.create_common_scenario()

    #     # checkin & checkout
    #     checkin = fields.date.today()
    #     checkout = fields.date.today() + datetime.timedelta(days=1)
    #     days = (checkout - checkin).days

    #     # set pricelist item for current day
    #     product_tmpl_id = self.test_room_type_double.product_id.product_tmpl_id.id
    #     pricelist_item = self.env["product.pricelist.item"].create(
    #         {
    #             "pricelist_id": self.test_pricelist.id,
    #             "date_start_consumption": checkin,
    #             "date_end_consumption": checkin,
    #             "compute_price": "fixed",
    #             "applied_on": "1_product",
    #             "product_tmpl_id": product_tmpl_id,
    #             "fixed_price": 38.0,
    #             "min_quantity": 4,
    #         }
    #     )

    #     # create folio wizard with partner id => pricelist & start-end dates
    #     booking_engine = self.env["pms.booking.engine"].create(
    #         {
    #             "start_date": checkin,
    #             "end_date": checkout,
    #             "partner_id": self.partner_id.id,
    #             "pricelist_id": self.test_pricelist.id,
    #         }
    #     )

    #     # availability items belonging to test property
    #     lines_availability_test = self.env["pms.folio.availability.wizard"].search(
    #         [
    #             ("room_type_id.pms_property_ids", "in", self.test_property.id),
    #         ]
    #     )

    #     test_cases = [
    #         {
    #             "num_rooms": 3,
    #             "expected_price": 3 * self.test_room_type_double.list_price * days,
    #         },
    #         {"num_rooms": 4, "expected_price": 4 * pricelist_item.fixed_price * days},
    #     ]
    #     import wdb; wdb.set_trace()
    #     for tc in test_cases:
    #         with self.subTest(k=tc):
    #             # ARRANGE
    #             # set value for room type double
    #             value = self.env["pms.num.rooms.selection"].search(
    #                 [
    #                     ("room_type_id", "=", self.test_room_type_double.id),
    #                     ("value", "=", tc["num_rooms"]),
    #                 ]
    #             )
    #             # ACT
    #             lines_availability_test[0].num_rooms_selected = value

    #             # ASSERT
    #             self.assertEqual(
    #                 booking_engine.total_price_folio,
    #                 tc["expected_price"],
    #                 "The total price calculation is wrong",
    #             )

    def test_check_create_folio(self):
        """
        Test that a folio is created correctly from the booking engine wizard.
        ------------
        The wizard is created with a partner_id, a pricelist, and start and end
        dates for property1. The availability items are searched for that property
        and in the first one a double room is set. The create_folio() method of the
        wizard is launched. The folios of the partner_id entered in the wizard are
        searched and it is verified that the folio exists.
        """

        # ARRANGE

        # checkin & checkout
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)

        # create folio wizard with partner id => pricelist & start-end dates
        booking_engine = self.env["pms.booking.engine"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pricelist_id": self.pricelist1.id,
                "pms_property_id": self.pms_property1.id,
                "channel_type_id": self.sale_channel_direct1.id,
            }
        )

        # availability items belonging to test property
        lines_availability_test = self.env["pms.folio.availability.wizard"].search(
            [
                ("room_type_id.pms_property_ids", "in", self.pms_property1.id),
            ]
        )
        # set one room type double
        value = self.env["pms.num.rooms.selection"].search(
            [
                ("room_type_id", "=", self.test_room_type_double.id),
                ("value", "=", 1),
            ]
        )
        lines_availability_test[0].num_rooms_selected = value

        # ACT
        booking_engine.create_folio()

        # ASSERT
        folio = self.env["pms.folio"].search([("partner_id", "=", self.partner_id.id)])

        self.assertTrue(folio, "Folio not created.")

    def test_check_create_reservations(self):
        """
        Check that reservations are created correctly from the booking engine wizard.
        ------------
        The wizard is created with a partner_id, a pricelist, and start and end
        dates for property1. The availability items are searched for that property
        and in the first one, two double rooms are set, which create two reservations
        too. The create_folio() method of the wizard is launched. The folios of the
        partner_id entered in the wizard are searched and it is verified that the two
        reservations of the folio was created.
        """

        # ARRANGE

        # checkin & checkout
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)

        # create folio wizard with partner id => pricelist & start-end dates
        booking_engine = self.env["pms.booking.engine"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pricelist_id": self.pricelist1.id,
                "pms_property_id": self.pms_property1.id,
                "channel_type_id": self.sale_channel_direct1.id,
            }
        )

        # availability items belonging to test property
        lines_availability_test = self.env["pms.folio.availability.wizard"].search(
            [
                ("room_type_id.pms_property_ids", "in", self.pms_property1.id),
            ]
        )
        # set one room type double
        value = self.env["pms.num.rooms.selection"].search(
            [
                ("room_type_id", "=", self.test_room_type_double.id),
                ("value", "=", 2),
            ]
        )
        lines_availability_test[0].num_rooms_selected = value
        lines_availability_test[0].value_num_rooms_selected = 2

        # ACT
        booking_engine.create_folio()

        folio = self.env["pms.folio"].search([("partner_id", "=", self.partner_id.id)])

        # ASSERT
        self.assertEqual(len(folio.reservation_ids), 2, "Reservations  not created.")

    def test_values_folio_created(self):
        """
        Check that the partner_id and pricelist_id values of the folio correspond
        to the partner_id and pricelist_id of the booking engine wizard that created
        the folio.
        -----------
        The wizard is created with a partner_id, a pricelist, and start and end
        dates for property1. The availability items are searched for that property
        and in the first one a double room are set. The create_folio() method of the
        wizard is launched. Then it is checked that the partner_id and the pricelist_id
        of the created folio are the same as the partner_id and the pricelist_id of the
        booking engine wizard.
        """

        # ARRANGE

        # checkin & checkout
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)

        # create folio wizard with partner id => pricelist & start-end dates
        booking_engine = self.env["pms.booking.engine"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pricelist_id": self.pricelist1.id,
                "pms_property_id": self.pms_property1.id,
                "channel_type_id": self.sale_channel_direct1.id,
            }
        )
        # availability items belonging to test property
        lines_availability_test = self.env["pms.folio.availability.wizard"].search(
            [
                ("room_type_id.pms_property_ids", "in", self.pms_property1.id),
            ]
        )
        # set one room type double
        value = self.env["pms.num.rooms.selection"].search(
            [
                ("room_type_id", "=", self.test_room_type_double.id),
                ("value", "=", 1),
            ]
        )
        lines_availability_test[0].num_rooms_selected = value
        lines_availability_test[0].value_num_rooms_selected = 1

        # ACT
        booking_engine.create_folio()
        vals = {
            "partner_id": self.partner_id.id,
            "pricelist_id": self.pricelist1.id,
        }
        folio = self.env["pms.folio"].search([("partner_id", "=", self.partner_id.id)])

        # ASSERT
        for key in vals:
            with self.subTest(k=key):
                self.assertEqual(
                    folio[key].id,
                    vals[key],
                    "The value of " + key + " is not correctly established",
                )

    def test_values_reservation_created(self):
        """
        Check with subtests that the values of the fields of a reservation created through
        a booking engine wizard are correct.
        --------------
        The wizard is created with a partner_id, a pricelist, and start and end
        dates for property1. The availability items are searched for that property
        and in the first one a double room are set. The create_folio() method of the
        wizard is launched. A vals dictionary is created with folio_id, checkin and
        checkout, room_type_id, partner_id, pricelist_id, and pms_property_id. Then
        the keys of this dictionary are crossed and it is verified that the values
        correspond with the values of the reservation created from the wizard .
        """

        # ARRANGE

        # checkin & checkout
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)

        # create folio wizard with partner id => pricelist & start-end dates
        booking_engine = self.env["pms.booking.engine"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pricelist_id": self.pricelist1.id,
                "pms_property_id": self.pms_property1.id,
                "channel_type_id": self.sale_channel_direct1.id,
            }
        )

        # availability items belonging to test property
        lines_availability_test = self.env["pms.folio.availability.wizard"].search(
            [
                ("room_type_id.pms_property_ids", "in", self.pms_property1.id),
            ]
        )
        # set one room type double
        value = self.env["pms.num.rooms.selection"].search(
            [
                ("room_type_id", "=", self.test_room_type_double.id),
                ("value", "=", 1),
            ]
        )
        lines_availability_test[0].num_rooms_selected = value
        lines_availability_test[0].value_num_rooms_selected = 1

        # ACT
        booking_engine.create_folio()

        folio = self.env["pms.folio"].search([("partner_id", "=", self.partner_id.id)])

        vals = {
            "folio_id": folio.id,
            "checkin": checkin,
            "checkout": checkout,
            "room_type_id": self.test_room_type_double.id,
            "partner_id": self.partner_id.id,
            "pricelist_id": folio.pricelist_id.id,
            "pms_property_id": self.pms_property1.id,
        }

        # ASSERT
        for reservation in folio.reservation_ids:
            for key in vals:
                with self.subTest(k=key):
                    self.assertEqual(
                        reservation[key].id
                        if key
                        in [
                            "folio_id",
                            "partner_id",
                            "pricelist_id",
                            "pms_property_id",
                            "room_type_id",
                        ]
                        else reservation[key],
                        vals[key],
                        "The value of " + key + " is not correctly established",
                    )

    def test_reservation_line_discounts(self):
        """
        Check that a discount applied to a reservation from a booking engine wizard
        is applied correctly in the reservation line.
        -----------------
        The wizard is created with a partner_id, a pricelist, a discount of 0.5 and
        start and end dates for property1. The availability items are searched for
        that property and in the first one a double room are set. The create_folio()
        method of the wizard is launched.Then it is verified that the discount of the
        reservation line is equal to the discount applied in the wizard.
        """

        # ARRANGE

        # checkin & checkout
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)
        discount = 0.5

        # create folio wizard with partner id => pricelist & start-end dates
        booking_engine = self.env["pms.booking.engine"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pricelist_id": self.pricelist1.id,
                "discount": discount,
                "pms_property_id": self.pms_property1.id,
                "channel_type_id": self.sale_channel_direct1.id,
            }
        )
        # availability items belonging to test property
        lines_availability_test = self.env["pms.folio.availability.wizard"].search(
            [
                ("room_type_id.pms_property_ids", "in", self.pms_property1.id),
            ]
        )
        # set one room type double
        value = self.env["pms.num.rooms.selection"].search(
            [
                ("room_type_id", "=", self.test_room_type_double.id),
                ("value", "=", 1),
            ]
        )
        lines_availability_test[0].num_rooms_selected = value
        lines_availability_test[0].value_num_rooms_selected = 1

        # ACT
        booking_engine.create_folio()

        folio = self.env["pms.folio"].search([("partner_id", "=", self.partner_id.id)])

        # ASSERT
        for line in folio.reservation_ids.reservation_line_ids:
            with self.subTest(k=line):
                self.assertEqual(
                    line.discount,
                    discount * 100,
                    "The discount is not correctly established",
                )

    def test_check_quota_avail(self):
        """
        Check that the availability for a room type in the booking engine
        wizard is correct by creating an availability_plan_rule with quota.
        -----------------
        An availability_plan_rule with quota = 1 is created for the double
        room type. A booking engine wizard is created with the checkin same
        date as the availability_plan_rule and with pricelist1, which also has
        the availability_plan set that contains the availability_plan_rule
        created before. Then the availability is searched for the type of
        double room which must be 1 because the availavility_plan_rule quota
        for that room is 1.
        """

        # ARRANGE

        # checkin & checkout
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)
        self.availability_plan1 = self.env["pms.availability.plan"].create(
            {
                "name": "Availability plan for TEST",
                "pms_pricelist_ids": [(6, 0, [self.pricelist1.id])],
            }
        )
        self.env["pms.availability.plan.rule"].create(
            {
                "quota": 1,
                "room_type_id": self.test_room_type_double.id,
                "availability_plan_id": self.availability_plan1.id,
                "date": fields.date.today(),
                "pms_property_id": self.pms_property1.id,
            }
        )
        # create folio wizard with partner id => pricelist & start-end dates
        booking_engine = self.env["pms.booking.engine"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pricelist_id": self.pricelist1.id,
                "pms_property_id": self.pms_property1.id,
                "channel_type_id": self.sale_channel_direct1.id,
            }
        )
        room_type_plan_avail = booking_engine.availability_results.filtered(
            lambda r: r.room_type_id.id == self.test_room_type_double.id
        ).num_rooms_available

        # ASSERT

        self.assertEqual(room_type_plan_avail, 1, "Quota not applied in Wizard Folio")

    def test_check_min_stay_avail(self):
        """
        Check that the availability for a room type in the booking engine
        wizard is correct by creating an availability_plan_rule with min_stay.
        -----------------
        An availability_plan_rule with min_stay = 3 is created for the double
        room type. A booking engine wizard is created with start_date = today
        and end_date = tomorrow. Then the availability is searched for the type of
        double room which must be 0 because the availability_plan_rule establishes
        that the min_stay is 3 days and the difference of days in the booking engine
        wizard is 1 .
        """

        # ARRANGE

        # checkin & checkout
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)
        # AVAILABILITY PLAN CREATION
        self.availability_plan1 = self.env["pms.availability.plan"].create(
            {
                "name": "Availability plan for TEST",
                "pms_pricelist_ids": [(6, 0, [self.pricelist1.id])],
            }
        )
        self.env["pms.availability.plan.rule"].create(
            {
                "min_stay": 3,
                "room_type_id": self.test_room_type_double.id,
                "availability_plan_id": self.availability_plan1.id,
                "date": fields.date.today(),
                "pms_property_id": self.pms_property1.id,
            }
        )

        # create folio wizard with partner id => pricelist & start-end dates
        booking_engine = self.env["pms.booking.engine"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pricelist_id": self.pricelist1.id,
                "pms_property_id": self.pms_property1.id,
                "channel_type_id": self.sale_channel_direct1.id,
            }
        )
        room_type_plan_avail = booking_engine.availability_results.filtered(
            lambda r: r.room_type_id.id == self.test_room_type_double.id
        ).num_rooms_available

        # ASSERT

        self.assertEqual(room_type_plan_avail, 0, "Quota not applied in Wizard Folio")

    @freeze_time("2015-05-05")
    def test_price_total_with_board_service(self):
        """
        In booking engine when in availability results choose a room or several
        and also choose a board service, the total price is calculated from price of the room,
        number of nights, board service included price and number of guests
        """
        # ARRANGE
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)

        self.product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
            }
        )
        self.board_service_test = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
            }
        )
        self.env["pms.board.service.line"].create(
            {
                "pms_board_service_id": self.board_service_test.id,
                "product_id": self.product_test1.id,
                "amount": 8,
            }
        )
        self.board_service_room_type = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.test_room_type_double.id,
                "pms_board_service_id": self.board_service_test.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        # self.board_service_room_type.flush()
        # ACT
        booking_engine = self.env["pms.booking.engine"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pricelist_id": self.pricelist1.id,
                "pms_property_id": self.pms_property1.id,
                "channel_type_id": self.sale_channel_direct1.id,
            }
        )

        lines_availability_test = booking_engine.availability_results.filtered(
            lambda r: r.room_type_id.id == self.test_room_type_double.id
        )

        value = self.env["pms.num.rooms.selection"].search(
            [
                ("room_type_id", "=", self.test_room_type_double.id),
                ("value", "=", 1),
            ]
        )
        lines_availability_test[0].num_rooms_selected = value
        lines_availability_test[0].value_num_rooms_selected = 1
        lines_availability_test[
            0
        ].board_service_room_id = self.board_service_room_type.id

        self.test_room_type_double.list_price = 25

        room_price = self.test_room_type_double.list_price
        days = (checkout - checkin).days
        board_service_price = self.board_service_test.amount
        room_capacity = self.test_room_type_double.get_room_type_capacity(
            self.pms_property1.id
        )
        expected_price = room_price * days + (
            board_service_price * room_capacity * days
        )

        # ASSERT
        self.assertEqual(
            lines_availability_test[0].price_per_room,
            expected_price,
            "The total price calculation is wrong",
        )

    @freeze_time("2014-05-05")
    def test_board_service_discount(self):
        """
        In booking engine when a discount is indicated it must be
        applied correctly on both reservation lines and board services,
        whether consumed after or before night
        """
        # ARRANGE
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)

        self.product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
            }
        )
        self.board_service_test = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
            }
        )
        self.env["pms.board.service.line"].create(
            {
                "pms_board_service_id": self.board_service_test.id,
                "product_id": self.product_test1.id,
                "amount": 8,
            }
        )
        self.board_service_room_type = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.test_room_type_double.id,
                "pms_board_service_id": self.board_service_test.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        discount = 15

        booking_engine = self.env["pms.booking.engine"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pricelist_id": self.pricelist1.id,
                "discount": discount,
                "pms_property_id": self.pms_property1.id,
                "channel_type_id": self.sale_channel_direct1.id,
            }
        )

        lines_availability_test = booking_engine.availability_results.filtered(
            lambda r: r.room_type_id.id == self.test_room_type_double.id
        )
        value = self.env["pms.num.rooms.selection"].search(
            [
                ("room_type_id", "=", self.test_room_type_double.id),
                ("value", "=", 1),
            ]
        )
        lines_availability_test[0].num_rooms_selected = value
        lines_availability_test[0].value_num_rooms_selected = 1
        lines_availability_test[
            0
        ].board_service_room_id = self.board_service_room_type.id

        # ACT
        booking_engine.create_folio()

        folio = self.env["pms.folio"].search([("partner_id", "=", self.partner_id.id)])

        # ASSERT
        for line in folio.service_ids.service_line_ids:
            if line.is_board_service:
                self.assertEqual(
                    line.discount,
                    discount * 100,
                    "The discount is not correctly established",
                )

    def test_check_folio_when_change_selection(self):
        """
        Check, when creating a folio from booking engine,
        if a room type is chosen and then deleted that selection
        isn`t registered on the folio and is properly unselected
        """
        # ARRANGE
        # CREATION OF ROOM TYPE (WITH ROOM TYPE CLASS)
        self.partner_id2 = self.env["res.partner"].create(
            {
                "name": "Brais",
                "mobile": "654665553",
                "email": "braistest@example.com",
            }
        )
        self.test_room_type_triple = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Triple Test",
                "default_code": "TRP_Test",
                "class_id": self.room_type_class1.id,
                "list_price": 60.0,
            }
        )

        # pms.room
        self.test_room1_triple = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Triple 301 test",
                "room_type_id": self.test_room_type_triple.id,
                "capacity": 3,
            }
        )
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)

        booking_engine = self.env["pms.booking.engine"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id2.id,
                "pricelist_id": self.pricelist1.id,
                "pms_property_id": self.pms_property1.id,
                "channel_type_id": self.sale_channel_direct1.id,
            }
        )

        lines_availability_test_double = booking_engine.availability_results.filtered(
            lambda r: r.room_type_id.id == self.test_room_type_double.id
        )
        value = self.env["pms.num.rooms.selection"].search(
            [
                ("room_type_id", "=", self.test_room_type_double.id),
                ("value", "=", 1),
            ]
        )
        lines_availability_test_double[0].num_rooms_selected = value
        lines_availability_test_double[0].value_num_rooms_selected = 1

        lines_availability_test_double[0].value_num_rooms_selected = 0

        lines_availability_test_triple = booking_engine.availability_results.filtered(
            lambda r: r.room_type_id.id == self.test_room_type_triple.id
        )
        value_triple = self.env["pms.num.rooms.selection"].search(
            [
                ("room_type_id", "=", self.test_room_type_triple.id),
                ("value", "=", 1),
            ]
        )
        lines_availability_test_triple[0].num_rooms_selected = value_triple
        lines_availability_test_triple[0].value_num_rooms_selected = 1

        # ACT
        booking_engine.create_folio()

        folio = self.env["pms.folio"].search([("partner_id", "=", self.partner_id2.id)])
        # ASSERT
        self.assertEqual(
            len(folio.reservation_ids),
            1,
            "Reservations of folio are incorrect",
        )

    def test_adding_board_services_are_saved_on_lines(self):
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)

        booking_engine = self.env["pms.booking.engine"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pricelist_id": self.pricelist1.id,
                "pms_property_id": self.pms_property1.id,
                "channel_type_id": self.sale_channel_direct1.id,
            }
        )
        booking_engine.availability_results.filtered(
            lambda r: r.room_type_id.id == self.test_room_type_double.id
        )
        self.assertTrue(False)
