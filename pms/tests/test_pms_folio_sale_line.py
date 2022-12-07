import datetime

from odoo import fields

from .common import TestPms


class TestPmsFolioSaleLine(TestPms):
    def setUp(self):
        """
        - common + room_type_avalability_plan
        """
        super().setUp()

        # create room type
        self.room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
                "price": 25,
            }
        )
        # create room
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

        self.product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
            }
        )
        self.product_test2 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
            }
        )
        self.board_service_test = self.board_service = self.env[
            "pms.board.service"
        ].create(
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
                "pms_room_type_id": self.room_type_double.id,
                "pms_board_service_id": self.board_service_test.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        self.extra_service = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": self.product_test2.id,
            }
        )

        self.sale_channel_direct1 = self.env["pms.sale.channel"].create(
            {
                "name": "Door",
                "channel_type": "direct",
            }
        )

    # RESERVATION LINES
    def test_comp_fsl_rooms_all_same_group(self):
        """
        check the grouping of the reservation lines on the sale line folio
        when the price, discount match-
        ------------
        reservation with 3 nights with the same price,
        should generate just 1 reservation sale line
        """
        # ARRANGE
        expected_sale_lines = 1

        # ACT
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "reservation_line_ids": [
                    (
                        0,
                        False,
                        {
                            "date": fields.date.today(),
                            "price": 20,
                            "discount": 10,
                        },
                    ),
                    (
                        0,
                        False,
                        {
                            "date": fields.date.today() + datetime.timedelta(days=1),
                            "price": 20,
                            "discount": 10,
                        },
                    ),
                    (
                        0,
                        False,
                        {
                            "date": fields.date.today() + datetime.timedelta(days=2),
                            "price": 20,
                            "discount": 10,
                        },
                    ),
                ],
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ASSERT
        self.assertEqual(
            expected_sale_lines,
            len(r_test.folio_id.sale_line_ids.filtered(lambda x: not x.display_type)),
            "Folio should contain {} sale lines".format(expected_sale_lines),
        )

    def test_comp_fsl_rooms_different_prices(self):
        """
        Check that a reservation with two nights and different prices per
        night generates two sale lines.
        ------------
        Create a reservation with a double room as a room type and 2 nights,
        which has a price of 25.0 per night. Then the price of one of the reservation
        lines is changed to 50.0. As there are two different prices per
        night in the reservation the sale lines of the folio should be 2 .
        """

        # ARRANGE
        expected_sale_lines = 2
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ACT
        r_test.reservation_line_ids[0].price = 50.0

        # ASSERT
        self.assertEqual(
            expected_sale_lines,
            len(r_test.folio_id.sale_line_ids.filtered(lambda x: not x.display_type)),
            "Folio should contain {} reservation sale lines".format(
                expected_sale_lines
            ),
        )

    def test_comp_fsl_rooms_different_discount(self):
        """
        Check that a reservation with two nights and different discount per
        night generates two sale lines.
        ------------
        Create a reservation with a double room as a room type and 2 nights, which has
        a default discount of 0 per night. Then the discount of one of the reservation
        lines is changed to 50.0. As there are two different discounts per night in the
        reservation the sale lines of the folio should be 2.
        """

        # ARRANGE
        expected_sale_lines = 2
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ACT
        r_test.reservation_line_ids[0].discount = 50.0

        # ASSERT
        self.assertEqual(
            expected_sale_lines,
            len(r_test.folio_id.sale_line_ids.filtered(lambda x: not x.display_type)),
            "Folio should contain {} reservation sale lines".format(
                expected_sale_lines
            ),
        )

    def test_comp_fsl_rooms_different_cancel_discount(self):
        """
        Check that a reservation with two nights and different cancel
        discount per night generates two sale lines.
        ------------
        Create a reservation with a double room as a room type and 2 nights,
        which has a default cancel discount of 0 per night. Then the cancel discount
        of one of the reservation lines is changed to 50.0. As there are two
        different cancel discount per night in the reservation the sale lines of
        the folio should be 2. As one of the reservation lines has a 100% cancel
        discount, the sale line should be 1 .
        """

        # ARRANGE
        expected_sale_lines = 2
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ACT
        r_test.reservation_line_ids[0].cancel_discount = 50.0

        # ASSERT
        self.assertEqual(
            expected_sale_lines,
            len(r_test.folio_id.sale_line_ids.filtered(lambda x: not x.display_type)),
            "Folio should contain {} reservation sale lines".format(
                expected_sale_lines
            ),
        )

    def test_comp_fsl_rooms_one_full_cancel_discount(self):
        """
        Check that a reservation with a 100% cancel discount on one night
        does not generate different sale lines.
        ----------------
        Create a reservation with a double room as a room type, which has
        a default cancel discount of 0 per night. Then the cancel discount
        of one of the reservation lines is changed to 100.0.
        """
        # ARRANGE
        expected_sale_lines = 1
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ACT
        r_test.reservation_line_ids[0].cancel_discount = 100.0
        r_test.flush()

        # ASSERT
        self.assertEqual(
            expected_sale_lines,
            len(r_test.folio_id.sale_line_ids.filtered(lambda x: not x.display_type)),
            "Folio should contain {} reservation sale lines".format(
                expected_sale_lines
            ),
        )

    def test_comp_fsl_rooms_increase_stay(self):
        """
        Check when adding a night to a reservation after creating it and this night
        has the same price, cancel and cancel discount values, the sales line that
        were created with the reservation are maintained.
        ---------
        Create a reservation of 2 nights for a double room. The value of the sale lines
        of that reservation is stored in a variable. Then one more night is added to the
        reservation and it is verified that the sale lines are the same as the value of
        the previously saved variable.
        """
        # ARRANGE
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r_test.flush()
        previous_folio_sale_line = r_test.folio_id.sale_line_ids.filtered(
            lambda x: not x.display_type
        )[0]

        # ACT
        r_test.checkout = datetime.datetime.now() + datetime.timedelta(days=4)
        r_test.flush()

        # ASSERT
        self.assertEqual(
            previous_folio_sale_line,
            r_test.folio_id.sale_line_ids.filtered(lambda x: not x.display_type)[0],
            "Previous records of reservation sales lines should not be "
            "deleted if it is not necessary",
        )

    def test_comp_fsl_rooms_decrease_stay(self):
        """
        Check when a night is removed from a reservation after creating
        it, the sales lines that were created with the reservation are kept.
        ---------
        Create a reservation of 2 nights for a double room. The value of the sale lines
        of that reservation is stored in a variable. Then it is removed one night at
        reservation and it is verified that the reservation sale lines are equal to the value of
        the previously saved variable.
        """
        # ARRANGE
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r_test.flush()
        previous_folio_sale_line = r_test.folio_id.sale_line_ids.filtered(
            lambda x: not x.display_type
        )[0]

        # ACT
        r_test.checkout = datetime.datetime.now() + datetime.timedelta(days=2)
        r_test.flush()

        # ASSERT
        self.assertEqual(
            previous_folio_sale_line,
            r_test.folio_id.sale_line_ids.filtered(lambda x: not x.display_type)[0],
            "Previous records of reservation sales lines should not be "
            "deleted if it is not necessary",
        )

    def test_comp_fsl_rooms_same_stay(self):
        """
        Check that when changing the price of all the reservation lines in a
        reservation, which before the change had the same price, discount
        and cancel discount values, the same sale lines that existed before
        the change are kept.
        ------------------
        Create a reservation of 2 nights for a double room with a price of 25.0.
        The value of the sale lines of that reservation is stored in a variable.
        Then the value of the price of all the reservation lines is changed to 50.0
        and it is verified that the reservation sale lines are equal to the value
        of the previously saved variable.
        """
        # ARRANGE
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r_test.flush()
        previous_folio_sale_line = r_test.folio_id.sale_line_ids.filtered(
            lambda x: not x.display_type
        )[0]

        # ACT
        r_test.reservation_line_ids.price = 50
        r_test.flush()

        # ASSERT
        self.assertEqual(
            previous_folio_sale_line,
            r_test.folio_id.sale_line_ids.filtered(lambda x: not x.display_type)[0],
            "Previous records of reservation sales lines should not be "
            "deleted if it is not necessary",
        )

    # BOARD SERVICES
    def test_comp_fsl_board_services_all_same_group(self):

        """
        Check that the board services of reservation with the same price, discount
        and cancel discount values, should only generate one sale line.
        ----------------
        Create a reservation of 2 nights, for a double room with a board service
        room per night. Then it is verified that the length of the sale lines of the
        board services in the reservation is equal to 1.
        """
        # ARRANGE
        expected_board_service_sale_lines = 1

        # ACT
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "board_service_room_id": self.board_service_room_type.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ASSERT
        self.assertEqual(
            expected_board_service_sale_lines,
            len(
                r_test.folio_id.sale_line_ids.filtered(
                    lambda x: x.reservation_id and x.service_id and x.is_board_service
                )
            ),
            "Folio should contain {} board service sale lines".format(
                expected_board_service_sale_lines
            ),
        )

    def test_comp_fsl_board_services_different_prices(self):
        """
        Check that the board services of reservation with different prices
        should generate several sale lines.
        ----------------
        Create a reservation of 2 nights, for a double room with a board service
        room per night. Then change the price of the first board service line to
        1.0 and it is verified that the length of the sale lines of the board services
        in the reservation is equal to 2 because there are 2 different board service
        prices in the reservation.
        """
        # ARRANGE
        expected_board_service_sale_lines = 2
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "board_service_room_id": self.board_service_room_type.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r_test.service_ids[0].service_line_ids[0].price_unit = 1.0

        # ASSERT
        self.assertEqual(
            expected_board_service_sale_lines,
            len(
                r_test.folio_id.sale_line_ids.filtered(
                    lambda x: not x.display_type and x.is_board_service
                )
            ),
            "Folio should contain {} board service sale lines".format(
                expected_board_service_sale_lines
            ),
        )

    def test_comp_fsl_board_services_different_discount(self):
        """
        Check that the board services of reservation with different discounts
        should generate several sale lines.
        ----------------
        Create a reservation of 2 nights, for a double room with a board service
        room per night. Then change the discount of the first board service line
        to 1.0 and it is verified that the length of the sale lines of the board services
        in the reservation is equal to 2 because there are 2 different board service
        discounts in the reservation.
        """
        # ARRANGE
        expected_board_service_sale_lines = 2
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "board_service_room_id": self.board_service_room_type.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ACT
        r_test.service_ids[0].service_line_ids[0].discount = 1.0

        # ASSERT
        self.assertEqual(
            expected_board_service_sale_lines,
            len(
                r_test.folio_id.sale_line_ids.filtered(
                    lambda x: not x.display_type and x.is_board_service
                )
            ),
            "Folio should contain {} board service sale lines".format(
                expected_board_service_sale_lines
            ),
        )

    def test_comp_fsl_board_services_different_cancel_discount(self):
        """
        Check that the board services of reservation with different cancel
        discounts should generate several sale lines.
        ----------------
        Create a reservation of 2 nights, for a double room with a board service
        room per night. Then change the cancel discount of the first board service line
        to 1.0 and it is verified that the length of the sale lines of the board services
        in the reservation is equal to 2 because there are 2 different board service
        cancel discounts in the reservation.
        """

        # ARRANGE
        expected_board_service_sale_lines = 2
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "board_service_room_id": self.board_service_room_type.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ACT
        r_test.service_ids[0].service_line_ids[0].cancel_discount = 1.0

        # ASSERT
        self.assertEqual(
            expected_board_service_sale_lines,
            len(
                r_test.folio_id.sale_line_ids.filtered(
                    lambda x: not x.display_type and x.is_board_service
                )
            ),
            "Folio should contain {} board service sale lines".format(
                expected_board_service_sale_lines
            ),
        )

    def test_comp_fsl_board_services_one_full_cancel_discount(self):
        """
        Check that the board services of reservation with 100% cancel
        discount should generate only 1 sale line.
        ----------------
        Create a reservation of 2 nights, for a double room with a board service
        room per night. Then change the cancel discount of the first board service line
        to 100.0 and it is verified that the length of the sale lines of the board services
        in the reservation is equal to 1.
        """

        # ARRANGE
        expected_board_service_sale_lines = 1
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "board_service_room_id": self.board_service_room_type.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ACT
        r_test.service_ids[0].service_line_ids[0].cancel_discount = 100.0

        # ASSERT
        self.assertEqual(
            expected_board_service_sale_lines,
            len(
                r_test.folio_id.sale_line_ids.filtered(
                    lambda x: not x.display_type and x.is_board_service
                )
            ),
            "Folio should contain {} board service sale lines".format(
                expected_board_service_sale_lines
            ),
        )

    def test_comp_fsl_board_services_increase_stay(self):
        """
        Check when adding a night to a reservation with board services room,
        after creating it and this board service has the same price, cancel
        and cancel discount values, the sale lines that were created with the
        reservation are kept.
        ---------
        Create a reservation of 2 nights for a double room with a board service.
        The value of the sale lines of that board services is stored in a variable.
        Then one more night is added to the reservation and it is verified that
        the sale lines are the same as the value of the previously saved variable.
        """

        # ARRANGE
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "board_service_room_id": self.board_service_room_type.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        previous_folio_board_service_sale_line = r_test.folio_id.sale_line_ids.filtered(
            lambda x: not x.display_type and x.is_board_service
        )[0]

        # ACT
        r_test.checkout = datetime.datetime.now() + datetime.timedelta(days=4)

        # ASSERT
        self.assertEqual(
            previous_folio_board_service_sale_line,
            r_test.folio_id.sale_line_ids.filtered(
                lambda x: not x.display_type and x.is_board_service
            )[0],
            "Previous records of board service sales lines should not be "
            "deleted if it is not necessary",
        )

    def test_comp_fsl_board_services_decrease_stay(self):
        """
        Check when removing a night to a reservation with board services room,
        after creating it and this board service has the same price, cancel
        and cancel discount values, the sale lines that were created with the
        reservation are kept.
        ---------
        Create a reservation of 2 nights for a double room with a board service.
        The value of the sale lines of that board services is stored in a variable.
        Then one night is removed to the reservation and it is verified that
        the sale lines are the same as the value of the previously saved variable.
        """

        # ARRANGE
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "board_service_room_id": self.board_service_room_type.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        previous_folio_board_service_sale_line = r_test.folio_id.sale_line_ids.filtered(
            lambda x: not x.display_type and x.is_board_service
        )[0]

        # ACT
        r_test.checkout = datetime.datetime.now() + datetime.timedelta(days=2)

        # ASSERT
        self.assertEqual(
            previous_folio_board_service_sale_line,
            r_test.folio_id.sale_line_ids.filtered(
                lambda x: not x.display_type and x.is_board_service
            )[0],
            "Previous records of board service sales lines should not be "
            "deleted if it is not necessary",
        )

    def test_comp_fsl_board_services_same_stay(self):
        """
        Check that when changing the price of all board services in a
        reservation, which before the change had the same price, discount
        and cancel discount values, the same sale lines that existed before
        the change are kept.
        ------------------
        Create a reservation of 2 nights for a double room with a board service
        price of 8.0. The value of the sale lines of the board services is stored
        in a variable. Then the value of the price of all the reservation board services
        is changed to 50 and it is verified that the reservation sale lines are equal to
        the value of the previously saved variable.
        """
        # ARRANGE
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "board_service_room_id": self.board_service_room_type.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        previous_folio_board_service_sale_line = r_test.folio_id.sale_line_ids.filtered(
            lambda x: not x.display_type and x.is_board_service
        )[0]

        # ACT
        r_test.service_ids.filtered(
            lambda x: x.is_board_service
        ).service_line_ids.price_unit = 50

        # ASSERT
        self.assertEqual(
            previous_folio_board_service_sale_line,
            r_test.folio_id.sale_line_ids.filtered(
                lambda x: not x.display_type and x.is_board_service
            )[0],
            "Previous records of board service sales lines should not be "
            "deleted if it is not necessary",
        )

    # RESERVATION EXTRA DAILY SERVICES
    def test_comp_fsl_res_extra_services_all_same_group(self):
        """
        Check that when adding a service that is not a board service to a
        reservation with the same price, cancel and cancel discount, the
        number of sales lines is kept.
        ------------------
        Create a 2 night reservation. Then a service is added with
        is_board_service = False and it is verified that the length of
        the sale lines of the reservation is 1.
        """
        # ARRANGE
        expected_extra_service_sale_lines = 1
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        # ACT
        r_test.service_ids = [(4, self.extra_service.id)]
        r_test.service_ids.service_line_ids.flush()

        # ASSERT
        self.assertEqual(
            expected_extra_service_sale_lines,
            len(
                r_test.folio_id.sale_line_ids.filtered(
                    lambda x: x.service_id == self.extra_service
                )
            ),
            "Folio should contain {} reservation service sale lines".format(
                expected_extra_service_sale_lines
            ),
        )

    def test_comp_fsl_res_extra_services_different_prices(self):
        """
        Check that a reservation of several nights and with different
        prices per day on services should generate several sale lines.
        -----------------
        Create a reservation for 2 nights. Then add a service to this
        reservation and the price of the first service line is changed
        to 44.5. It is verified that the length of the reservation's sale
        lines is equal to 2, because there are two different prices per day
        for service lines.
        """

        # ARRANGE
        expected_extra_service_sale_lines = 2
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r_test.service_ids = [(4, self.extra_service.id)]
        r_test.service_ids.service_line_ids.flush()

        # ACT
        r_test.service_ids.service_line_ids[0].price_unit = 44.5
        r_test.service_ids.service_line_ids.flush()

        # ASSERT
        self.assertEqual(
            expected_extra_service_sale_lines,
            len(
                r_test.folio_id.sale_line_ids.filtered(
                    lambda x: x.service_id == self.extra_service
                )
            ),
            "Folio should contain {} reservation service sale lines".format(
                expected_extra_service_sale_lines
            ),
        )

    def test_comp_fsl_res_extra_services_different_discount(self):
        """
        Check that a reservation of several nights and with different
        discount per day on services should generate several sale lines.
        -----------------
        Create a reservation for 2 nights. Then add a service to this
        reservation and the discount of the first service line is changed
        to 44.5. It is verified that the length of the reservation's sale
        lines is equal to 2, because there are two different discounts per day
        for service lines.
        """

        # ARRANGE
        expected_extra_service_sale_lines = 2
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r_test.service_ids = [(4, self.extra_service.id)]
        r_test.service_ids.service_line_ids.flush()

        # ACT
        r_test.service_ids.service_line_ids[0].discount = 44.5
        r_test.service_ids.service_line_ids.flush()

        # ASSERT
        self.assertEqual(
            expected_extra_service_sale_lines,
            len(
                r_test.folio_id.sale_line_ids.filtered(
                    lambda x: x.service_id == self.extra_service
                )
            ),
            "Folio should contain {} reservation service sale lines".format(
                expected_extra_service_sale_lines
            ),
        )

    def test_comp_fsl_res_extra_services_different_cancel_discount(self):
        """
        Check that a reservation of several nights and with different
        cancel discount per day on services should generate several sale
        lines.
        -----------------
        Create a reservation for 2 nights. Then add a service to this
        reservation and the cancel discount of the first service line is changed
        to 44.5. It is verified that the length of the reservation's sale
        lines is equal to 2, because there are two different cancel discounts per
        day for service lines.
        """

        # ARRANGE
        expected_extra_service_sale_lines = 2
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r_test.service_ids = [(4, self.extra_service.id)]
        r_test.service_ids.service_line_ids.flush()

        # ACT
        r_test.service_ids.service_line_ids[0].cancel_discount = 44.5
        r_test.service_ids.service_line_ids.flush()

        # ASSERT
        self.assertEqual(
            expected_extra_service_sale_lines,
            len(
                r_test.folio_id.sale_line_ids.filtered(
                    lambda x: x.service_id == self.extra_service
                )
            ),
            "Folio should contain {} reservation service sale lines".format(
                expected_extra_service_sale_lines
            ),
        )

    def test_comp_fsl_res_extra_services_one_full_cancel_discount(self):
        """
        Check that a reservation of several nights and with a 100% cancel
        discount for a service should generate only 1 sale line.
        -----------------
        Create a reservation for 2 nights. Then add a service to this
        reservation and the cancel discount of the first service line is changed
        to 100%. It is verified that the length of the reservation sale
        lines is equal to 1.
        """

        # ARRANGE
        expected_extra_service_sale_lines = 1
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r_test.service_ids = [(4, self.extra_service.id)]
        r_test.service_ids.service_line_ids.flush()

        # ACT
        r_test.service_ids.service_line_ids[0].cancel_discount = 100
        r_test.service_ids.service_line_ids.flush()

        # ASSERT
        self.assertEqual(
            expected_extra_service_sale_lines,
            len(
                r_test.folio_id.sale_line_ids.filtered(
                    lambda x: x.service_id == self.extra_service
                )
            ),
            "Folio should contain {} reservation service sale lines".format(
                expected_extra_service_sale_lines
            ),
        )

    def test_comp_fsl_res_extra_services_increase_stay(self):
        """
        Check when adding a night to a reservation after creating it and this services
        has the same price, cancel and cancel discount values, the sales line that
        were created with the reservation are maintained.
        ---------
        Create a reservation of 2 nights for a double room and add a service to this
        reservation. The value of the sale lines of that reservation services is stored
        in a variable. Then one more night is added to the reservation and it is verified
        that the reservation service sale lines are the same as the value of the previously
        saved variable.
        """

        # ARRANGE
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r_test.service_ids = [(4, self.extra_service.id)]
        r_test.service_ids.service_line_ids.flush()
        previous_folio_extra_service_sale_line = r_test.folio_id.sale_line_ids.filtered(
            lambda x: x.service_id == self.extra_service
        )[0]

        # ACT
        r_test.checkout = datetime.datetime.now() + datetime.timedelta(days=4)
        r_test.service_ids.service_line_ids.flush()

        # ASSERT
        self.assertEqual(
            previous_folio_extra_service_sale_line,
            r_test.folio_id.sale_line_ids.filtered(
                lambda x: x.service_id == self.extra_service
            ),
            "Previous records of reservation service sales lines should not be "
            "deleted if it is not necessary",
        )

    def test_comp_fsl_res_extra_services_decrease_stay(self):
        """
        Check when removing a night to a reservation after creating it and this services
        has the same price, cancel and cancel discount values, the sales line that
        were created with the reservation are maintained.
        ---------
        Create a reservation of 2 nights for a double room and add a service to this
        reservation. The value of the sale lines of the services is stored
        in a variable. Then one night is removed to the reservation and it is verified
        that the reservation service sale lines are the same as the value of the previously
        saved variable.
        """
        # ARRANGE
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r_test.service_ids = [(4, self.extra_service.id)]
        r_test.service_ids.service_line_ids.flush()
        previous_folio_extra_service_sale_line = r_test.folio_id.sale_line_ids.filtered(
            lambda x: x.service_id == self.extra_service
        )[0]

        # ACT
        r_test.checkout = datetime.datetime.now() + datetime.timedelta(days=2)
        r_test.service_ids.service_line_ids.flush()

        # ASSERT
        self.assertEqual(
            previous_folio_extra_service_sale_line,
            r_test.folio_id.sale_line_ids.filtered(
                lambda x: x.service_id == self.extra_service
            ),
            "Previous records of reservation service sales lines should not be "
            "deleted if it is not necessary",
        )

    def test_comp_fsl_res_extra_services_same_stay(self):
        # TEST CASE
        # Price is changed for all reservation services of a 2-night reservation.
        # But price, discount & cancel discount after the change is the same
        #   for all nights.
        # Should keep the same reservation service sales line record.
        """
        Check that when changing the price of all services in a
        reservation, which before the change had the same price, discount
        and cancel discount values, the same sale lines that existed before
        the change are kept.
        ------------------
        Create a reservation of 2 nights for a double room and add a service to this
        reservation. The value of the sale lines of the services is stored
        in a variable. Then the value of the price of all the reservation services
        is changed to 50 and it is verified that the reservation service sale lines
        are equal to the value of the previously saved variable.
        """

        # ARRANGE
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r_test.service_ids = [(4, self.extra_service.id)]
        r_test.service_ids.service_line_ids.flush()
        previous_folio_extra_service_sale_line = r_test.folio_id.sale_line_ids.filtered(
            lambda x: x.service_id == self.extra_service
        )[0]

        # ACT
        r_test.service_ids.filtered(
            lambda x: x.id == self.extra_service.id
        ).service_line_ids.price_unit = 50
        r_test.service_ids.service_line_ids.flush()

        # ASSERT
        self.assertEqual(
            previous_folio_extra_service_sale_line,
            r_test.folio_id.sale_line_ids.filtered(
                lambda x: x.service_id == self.extra_service
            ),
            "Previous records of reservation service sales lines should not be "
            "deleted if it is not necessary",
        )

    # FOLIO EXTRA SERVICES
    def test_comp_fsl_fol_extra_services_one(self):
        # TEST CASE
        # Folio with extra services
        # should generate 1 folio service sale line
        """
        Check that when adding a service that is not a board service to a
        folio with the same price, cancel and cancel discount, the number
        of sales lines is kept.
        ------------------
        Create a 2 night reservation. Then a service is added with
        is_board_service = False and it is verified that the length of
        the sale lines of the folio is 1.
        """
        # ARRANGE
        expected_folio_service_sale_lines = 1
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ACT
        r_test.folio_id.service_ids = [(4, self.extra_service.id)]
        r_test.folio_id.service_ids.service_line_ids.flush()

        # ASSERT
        self.assertEqual(
            expected_folio_service_sale_lines,
            len(
                r_test.folio_id.sale_line_ids.filtered(
                    lambda x: x.service_id == self.extra_service
                )
            ),
            "Folio should contain {} folio service sale lines".format(
                expected_folio_service_sale_lines
            ),
        )

    def test_comp_fsl_fol_extra_services_two(self):
        """
        Check that when adding several services to a folio,
        several sale lines should be generated on the folio.
        -----------------
        Create a 2 night reservation. Two services are added
        to the reservation and it is verified that the length
        of the folio sale lines is equal to 2.
        """

        # ARRANGE
        expected_folio_service_sale_lines = 2
        product_test2 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
            }
        )

        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        extra_service2 = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": product_test2.id,
            }
        )

        # ACT
        r_test.folio_id.service_ids = [(4, self.extra_service.id)]
        r_test.folio_id.service_ids = [(4, extra_service2.id)]
        r_test.folio_id.service_ids.service_line_ids.flush()

        # ASSERT
        self.assertEqual(
            expected_folio_service_sale_lines,
            len(
                r_test.folio_id.sale_line_ids.filtered(
                    lambda x: not x.reservation_id and not x.display_type
                )
            ),
            "Folio should contain {} folio service sale lines".format(
                expected_folio_service_sale_lines
            ),
        )

    def test_no_sale_lines_staff_reservation(self):
        """
        Check that the sale_line_ids of a folio whose reservation
        is of type 'staff' are not created.
        -----
        A reservation is created with the reservation_type field
        with value 'staff'. Then it is verified that the
        sale_line_ids of the folio created with the creation of
        the reservation are equal to False.
        """
        # ARRANGE
        self.partner1 = self.env["res.partner"].create({"name": "Alberto"})
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=3)
        # ACT
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": checkin,
                "checkout": checkout,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "reservation_type": "staff",
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        # ASSERT
        self.assertFalse(
            reservation.folio_id.sale_line_ids,
            "Folio sale lines should not be generated for a staff type reservation ",
        )

    def test_no_sale_lines_out_reservation(self):
        """
        Check that the sale_line_ids of a folio whose reservation
        is of type 'out' are not created.
        -----
        A reservation is created with the reservation_type field
        with value 'out'. Then it is verified that the
        sale_line_ids of the folio created with the creation of
        the reservation are equal to False.
        """
        # ARRANGE
        self.partner1 = self.env["res.partner"].create({"name": "Alberto"})
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=3)
        closure_reason = self.env["room.closure.reason"].create(
            {
                "name": "test closure reason",
                "description": "test clopsure reason description",
            }
        )
        # ACT
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": checkin,
                "checkout": checkout,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "reservation_type": "out",
                "closure_reason_id": closure_reason.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        # ASSERT
        self.assertFalse(
            reservation.folio_id.sale_line_ids,
            "Folio sale lines should not be generated for a out of service type reservation ",
        )
