import datetime

from .common import TestPms


class TestPmsFolioSaleLine(TestPms):
    def create_common_scenario(self):
        # create a room type availability
        self.room_type_availability = self.env["pms.availability.plan"].create(
            {"name": "Availability plan for TEST"}
        )

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
            {"name": "Room", "default_code": "ROOM"}
        )

        # create room type
        self.room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.property.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class.id,
                "price": 25,
            }
        )
        # create room
        self.room1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.property.id,
                "name": "Double 101",
                "room_type_id": self.room_type_double.id,
                "capacity": 2,
            }
        )

    # RESERVATION LINES
    def test_comp_fsl_rooms_all_same_group(self):
        # TEST CASE
        # 2-night reservation and same price, discount & cancel_discount for
        # all nights
        # should generate just 1 reservation sale line

        # ARRANGE
        expected_sale_lines = 1
        self.create_common_scenario()

        # ACT
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )

        # ASSERT
        self.assertEqual(
            expected_sale_lines,
            len(r_test.folio_id.sale_line_ids.filtered(lambda x: not x.display_type)),
            "Folio should contain {} sale lines".format(expected_sale_lines),
        )

    def test_comp_fsl_rooms_different_prices(self):
        # TEST CASE
        # 2-night reservation and different price per night
        #   should generate 2 reservation sale lines

        # ARRANGE
        expected_sale_lines = 2
        self.create_common_scenario()
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
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
        # TEST CASE
        # 2-night reservationwith different discount per night
        # should generate 2 reservation sale lines

        # ARRANGE
        expected_sale_lines = 2
        self.create_common_scenario()
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
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
        # TEST CASE
        # 2-night-reservation with different discount per night
        # should generate 2 reservation sale lines

        # ARRANGE
        expected_sale_lines = 2
        self.create_common_scenario()
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
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
        # TEST CASE
        # 2-night reservation with 100% cancelled discount for 1 night
        # should generate just 1 reservation sale line because the
        #   full cancel discount shouldn't be present @ invoice lines

        # ARRANGE
        expected_sale_lines = 1
        self.create_common_scenario()
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
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
        # TEST CASE
        # 2-night reservation increases 1 night with the same price,
        # discount and cancel discount for all the reservation nights
        # Should keep the same reservation sales line record.

        # ARRANGE
        self.create_common_scenario()
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
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
        # TEST CASE
        # 2-night reservation decreases 1 night with the same price,
        # discount & cancel_discount for all the reservation nights
        # Should keep the same reservation sales line record.

        # ARRANGE
        self.create_common_scenario()
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
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
        # TEST CASE
        # Price is changed for all nights of a 2-night reservation. But
        #   price, discount & cancel discount after the change is the same
        #   for all nights.
        # Should keep the same reservation sales line record.

        # ARRANGE
        self.create_common_scenario()
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
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
        # TEST CASE
        # 2-night reservation and same price, discount & cancel_discount for
        # all reservation board services
        # should generate just 1 board service sale line

        # ARRANGE
        expected_board_service_sale_lines = 1
        self.create_common_scenario()
        product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
            }
        )
        board_service_test = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
            }
        )
        self.env["pms.board.service.line"].create(
            {
                "pms_board_service_id": board_service_test.id,
                "product_id": product_test1.id,
                "amount": 8,
            }
        )
        board_service_room_type = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type_double.id,
                "pms_board_service_id": board_service_test.id,
            }
        )

        # ACT
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "board_service_room_id": board_service_room_type.id,
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
        # TEST CASE
        # 2-night reservation and different price per day on board services
        # should generate just 1 board service sale line

        # ARRANGE
        expected_board_service_sale_lines = 2
        self.create_common_scenario()
        product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
            }
        )

        board_service_test = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
            }
        )
        self.env["pms.board.service.line"].create(
            {
                "pms_board_service_id": board_service_test.id,
                "product_id": product_test1.id,
                "amount": 8,
            }
        )
        board_service_room_type = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type_double.id,
                "pms_board_service_id": board_service_test.id,
            }
        )
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "board_service_room_id": board_service_room_type.id,
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
        # TEST CASE
        # 2-night reservation and different discount per day on board services
        # should generate 2 board service sale lines

        # ARRANGE
        expected_board_service_sale_lines = 2
        self.create_common_scenario()
        product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
            }
        )

        board_service_test = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
            }
        )
        self.env["pms.board.service.line"].create(
            {
                "pms_board_service_id": board_service_test.id,
                "product_id": product_test1.id,
                "amount": 8,
            }
        )
        board_service_room_type = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type_double.id,
                "pms_board_service_id": board_service_test.id,
            }
        )
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "board_service_room_id": board_service_room_type.id,
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
        # TEST CASE
        # 2-night reservation and different cancel discount per day on
        #   board services
        # should generate 2 board service sale lines

        # ARRANGE
        expected_board_service_sale_lines = 2
        self.create_common_scenario()
        product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
            }
        )

        board_service_test = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
            }
        )
        self.env["pms.board.service.line"].create(
            {
                "pms_board_service_id": board_service_test.id,
                "product_id": product_test1.id,
                "amount": 8,
            }
        )
        board_service_room_type = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type_double.id,
                "pms_board_service_id": board_service_test.id,
            }
        )
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "board_service_room_id": board_service_room_type.id,
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
        # TEST CASE
        # 2-night reservation with 100% cancelled discount for 1 board service
        # should generate just 1 board service sale line because the
        #   full cancel discount shouldn't be present @ invoice lines

        # ARRANGE
        expected_board_service_sale_lines = 1
        self.create_common_scenario()
        product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
            }
        )

        board_service_test = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
            }
        )
        self.env["pms.board.service.line"].create(
            {
                "pms_board_service_id": board_service_test.id,
                "product_id": product_test1.id,
                "amount": 8,
            }
        )
        board_service_room_type = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type_double.id,
                "pms_board_service_id": board_service_test.id,
            }
        )
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "board_service_room_id": board_service_room_type.id,
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
        # TEST CASE
        # 2-night reservation increases 1 night with the same price,
        # discount & cancel_discount for all the board services
        # Should keep the same board service sales line record.

        # ARRANGE
        self.create_common_scenario()
        product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
            }
        )
        board_service_test = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
            }
        )
        self.env["pms.board.service.line"].create(
            {
                "pms_board_service_id": board_service_test.id,
                "product_id": product_test1.id,
                "amount": 8,
            }
        )
        board_service_room_type = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type_double.id,
                "pms_board_service_id": board_service_test.id,
            }
        )
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "board_service_room_id": board_service_room_type.id,
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
        # TEST CASE
        # 2-night reservation decreases 1 night with the same price,
        # discount & cancel_discount for all the board services
        # Should keep the same board service sales line record.

        # ARRANGE
        self.create_common_scenario()
        product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
            }
        )

        board_service_test = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
            }
        )

        self.env["pms.board.service.line"].create(
            {
                "pms_board_service_id": board_service_test.id,
                "product_id": product_test1.id,
                "amount": 8,
            }
        )

        board_service_room_type = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type_double.id,
                "pms_board_service_id": board_service_test.id,
            }
        )

        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "board_service_room_id": board_service_room_type.id,
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
        # TEST CASE
        # Price is changed for all board services of a 2-night reservation.
        # But price, discount & cancel discount after the change is the same
        #   for all nights.
        # Should keep the same board service sales line record.

        # ARRANGE
        self.create_common_scenario()
        product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
            }
        )

        board_service_test = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
            }
        )

        self.env["pms.board.service.line"].create(
            {
                "pms_board_service_id": board_service_test.id,
                "product_id": product_test1.id,
                "amount": 8,
            }
        )

        board_service_room_type = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type_double.id,
                "pms_board_service_id": board_service_test.id,
            }
        )

        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "board_service_room_id": board_service_room_type.id,
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
        # TEST CASE
        # 2-night reservation and same price, discount & cancel_discount for
        # all reservation services
        # should generate just 1 reservation service sale line

        # ARRANGE
        expected_extra_service_sale_lines = 1
        self.create_common_scenario()
        product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
                # REVIEW 'before' -> create pms.service.line with price 0.0
            }
        )
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        extra_service = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": product_test1.id,
            }
        )

        # ACT
        r_test.service_ids = [(4, extra_service.id)]
        r_test.service_ids.service_line_ids.flush()

        # ASSERT
        self.assertEqual(
            expected_extra_service_sale_lines,
            len(
                r_test.folio_id.sale_line_ids.filtered(
                    lambda x: x.service_id == extra_service
                )
            ),
            "Folio should contain {} reservation service sale lines".format(
                expected_extra_service_sale_lines
            ),
        )

    def test_comp_fsl_res_extra_services_different_prices(self):
        # TEST CASE
        # 2-night reservation and different price per day on services
        # should generate just 1 reservation service sale line

        # ARRANGE
        expected_extra_service_sale_lines = 2
        self.create_common_scenario()
        product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
                # REVIEW 'before' -> create pms.service.line with price 0.0
            }
        )
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        extra_service = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": product_test1.id,
            }
        )
        r_test.service_ids = [(4, extra_service.id)]
        r_test.service_ids.service_line_ids.flush()

        # ACT
        r_test.service_ids.service_line_ids[0].price_unit = 44.5
        r_test.service_ids.service_line_ids.flush()

        # ASSERT
        self.assertEqual(
            expected_extra_service_sale_lines,
            len(
                r_test.folio_id.sale_line_ids.filtered(
                    lambda x: x.service_id == extra_service
                )
            ),
            "Folio should contain {} reservation service sale lines".format(
                expected_extra_service_sale_lines
            ),
        )

    def test_comp_fsl_res_extra_services_different_discount(self):
        # TEST CASE
        # 2-night reservation and different discount per day on reservation services
        # should generate 2 reservation service sale lines

        # ARRANGE
        expected_extra_service_sale_lines = 2
        self.create_common_scenario()
        product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
                # REVIEW 'before' -> create pms.service.line with price 0.0
            }
        )
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        extra_service = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": product_test1.id,
            }
        )
        r_test.service_ids = [(4, extra_service.id)]
        r_test.service_ids.service_line_ids.flush()

        # ACT
        r_test.service_ids.service_line_ids[0].discount = 44.5
        r_test.service_ids.service_line_ids.flush()

        # ASSERT
        self.assertEqual(
            expected_extra_service_sale_lines,
            len(
                r_test.folio_id.sale_line_ids.filtered(
                    lambda x: x.service_id == extra_service
                )
            ),
            "Folio should contain {} reservation service sale lines".format(
                expected_extra_service_sale_lines
            ),
        )

    def test_comp_fsl_res_extra_services_different_cancel_discount(self):
        # TEST CASE
        # 2-night reservation and different cancel discount per day on
        #   reservation services
        # should generate 2 reservation service sale lines

        # ARRANGE
        expected_extra_service_sale_lines = 2
        self.create_common_scenario()
        product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
                # REVIEW 'before' -> create pms.service.line with price 0.0
            }
        )
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        extra_service = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": product_test1.id,
            }
        )
        r_test.service_ids = [(4, extra_service.id)]
        r_test.service_ids.service_line_ids.flush()

        # ACT
        r_test.service_ids.service_line_ids[0].cancel_discount = 44.5
        r_test.service_ids.service_line_ids.flush()

        # ASSERT
        self.assertEqual(
            expected_extra_service_sale_lines,
            len(
                r_test.folio_id.sale_line_ids.filtered(
                    lambda x: x.service_id == extra_service
                )
            ),
            "Folio should contain {} reservation service sale lines".format(
                expected_extra_service_sale_lines
            ),
        )

    def test_comp_fsl_res_extra_services_one_full_cancel_discount(self):
        # TEST CASE
        # 2-night reservation with 100% cancelled discount for 1 reservation
        #   service
        # should generate just 1 reservation service sale line because the
        #   full cancel discount shouldn't be present @ invoice lines

        # ARRANGE
        expected_extra_service_sale_lines = 1
        self.create_common_scenario()
        product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
                # REVIEW 'before' -> create pms.service.line with price 0.0
            }
        )
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        extra_service = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": product_test1.id,
            }
        )
        r_test.service_ids = [(4, extra_service.id)]
        r_test.service_ids.service_line_ids.flush()

        # ACT
        r_test.service_ids.service_line_ids[0].cancel_discount = 100
        r_test.service_ids.service_line_ids.flush()

        # ASSERT
        self.assertEqual(
            expected_extra_service_sale_lines,
            len(
                r_test.folio_id.sale_line_ids.filtered(
                    lambda x: x.service_id == extra_service
                )
            ),
            "Folio should contain {} reservation service sale lines".format(
                expected_extra_service_sale_lines
            ),
        )

    def test_comp_fsl_res_extra_services_increase_stay(self):
        # TEST CASE
        # 2-night reservation increases 1 night with the same price,
        # discount & cancel_discount for all the reservation services
        # Should keep the same reservation service sales line record.

        # ARRANGE
        self.create_common_scenario()
        product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
                # REVIEW 'before' -> create pms.service.line with price 0.0
            }
        )
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        extra_service = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": product_test1.id,
            }
        )
        r_test.service_ids = [(4, extra_service.id)]
        r_test.service_ids.service_line_ids.flush()
        previous_folio_extra_service_sale_line = r_test.folio_id.sale_line_ids.filtered(
            lambda x: x.service_id == extra_service
        )[0]

        # ACT
        r_test.checkout = datetime.datetime.now() + datetime.timedelta(days=4)
        r_test.service_ids.service_line_ids.flush()

        # ASSERT
        self.assertEqual(
            previous_folio_extra_service_sale_line,
            r_test.folio_id.sale_line_ids.filtered(
                lambda x: x.service_id == extra_service
            ),
            "Previous records of reservation service sales lines should not be "
            "deleted if it is not necessary",
        )

    def test_comp_fsl_res_extra_services_decrease_stay(self):
        # TEST CASE
        # 2-night reservation decreases 1 night with the same price,
        # discount & cancel_discount for all the reservation services
        # Should keep the same reservation service sales line record.

        # ARRANGE
        self.create_common_scenario()
        product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
                # REVIEW 'before' -> create pms.service.line with price 0.0
            }
        )
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        extra_service = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": product_test1.id,
            }
        )
        r_test.service_ids = [(4, extra_service.id)]
        r_test.service_ids.service_line_ids.flush()
        previous_folio_extra_service_sale_line = r_test.folio_id.sale_line_ids.filtered(
            lambda x: x.service_id == extra_service
        )[0]

        # ACT
        r_test.checkout = datetime.datetime.now() + datetime.timedelta(days=2)
        r_test.service_ids.service_line_ids.flush()

        # ASSERT
        self.assertEqual(
            previous_folio_extra_service_sale_line,
            r_test.folio_id.sale_line_ids.filtered(
                lambda x: x.service_id == extra_service
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

        # ARRANGE
        self.create_common_scenario()
        product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
                # REVIEW 'before' -> create pms.service.line with price 0.0
            }
        )
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        extra_service = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": product_test1.id,
            }
        )
        r_test.service_ids = [(4, extra_service.id)]
        r_test.service_ids.service_line_ids.flush()
        previous_folio_extra_service_sale_line = r_test.folio_id.sale_line_ids.filtered(
            lambda x: x.service_id == extra_service
        )[0]

        # ACT
        r_test.service_ids.filtered(
            lambda x: x.id == extra_service
        ).service_line_ids.price_unit = 50
        r_test.service_ids.service_line_ids.flush()

        # ASSERT
        self.assertEqual(
            previous_folio_extra_service_sale_line,
            r_test.folio_id.sale_line_ids.filtered(
                lambda x: x.service_id == extra_service
            ),
            "Previous records of reservation service sales lines should not be "
            "deleted if it is not necessary",
        )

    # FOLIO EXTRA SERVICES
    def test_comp_fsl_fol_extra_services_one(self):
        # TEST CASE
        # Folio with extra services
        # should generate 1 folio service sale line

        # ARRANGE
        expected_folio_service_sale_lines = 1
        self.create_common_scenario()
        product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
            }
        )
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        extra_service = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": product_test1.id,
            }
        )

        # ACT
        r_test.folio_id.service_ids = [(4, extra_service.id)]
        r_test.folio_id.service_ids.service_line_ids.flush()

        # ASSERT
        self.assertEqual(
            expected_folio_service_sale_lines,
            len(
                r_test.folio_id.sale_line_ids.filtered(
                    lambda x: x.service_id == extra_service
                )
            ),
            "Folio should contain {} folio service sale lines".format(
                expected_folio_service_sale_lines
            ),
        )

    def test_comp_fsl_fol_extra_services_two(self):
        # TEST CASE
        # Folio with 2 extra services (but the same product)
        # Should generate 2 folio service sale line

        # ARRANGE
        expected_folio_service_sale_lines = 2
        self.create_common_scenario()
        product_test1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
            }
        )
        product_test2 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
            }
        )

        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        extra_service1 = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": product_test1.id,
            }
        )

        extra_service2 = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": product_test2.id,
            }
        )

        # ACT
        r_test.folio_id.service_ids = [(4, extra_service1.id)]
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
