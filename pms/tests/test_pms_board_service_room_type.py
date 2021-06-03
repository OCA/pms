from odoo.tests import common


class TestPmsBoardServiceRoomType(common.SavepointCase):
    def _create_common_scenario(self):
        self.company1 = self.env["res.company"].create(
            {
                "name": "Pms_Company_Test",
            }
        )
        self.folio_sequence = self.env["ir.sequence"].create(
            {
                "name": "PMS Folio",
                "code": "pms.folio",
                "padding": 4,
                "company_id": self.company1.id,
            }
        )
        self.reservation_sequence = self.env["ir.sequence"].create(
            {
                "name": "PMS Reservation",
                "code": "pms.reservation",
                "padding": 4,
                "company_id": self.company1.id,
            }
        )
        self.checkin_sequence = self.env["ir.sequence"].create(
            {
                "name": "PMS Checkin",
                "code": "pms.checkin.partner",
                "padding": 4,
                "company_id": self.company1.id,
            }
        )
        self.property1 = self.env["pms.property"].create(
            {
                "name": "Pms_property_test1",
                "company_id": self.company1.id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )
        self.property2 = self.env["pms.property"].create(
            {
                "name": "Pms_property_test2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )
        self.room_type_availability = self.env["pms.availability.plan"].create(
            {"name": "Availability plan for TEST"}
        )

        # create room type class
        self.room_type_class = self.env["pms.room.type.class"].create(
            {"name": "Room", "default_code": "ROOM"}
        )

    def test_create_rt_props_gt_bs_props(self):
        # TEST CASE
        # Create board service for a room type and the room type
        # have MORE properties than the board service.
        # Record of board_service_room_type should contain the
        # board service properties.

        # ARRANGE
        self._create_common_scenario()
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.property1.id, self.property2.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class.id,
                "price": 25,
            }
        )
        board_service_test = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
                "pms_property_ids": [self.property1.id],
            }
        )
        # ACT
        new_bsrt = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": room_type_double.id,
                "pms_board_service_id": board_service_test.id,
            }
        )
        # ASSERT
        self.assertEqual(
            new_bsrt.pms_property_ids.ids,
            board_service_test.pms_property_ids.ids,
            "Record of board_service_room_type should contain the"
            " board service properties.",
        )

    def test_create_rt_props_lt_bs_props(self):
        # TEST CASE
        # Create board service for a room type and the room type
        # have LESS properties than the board service.
        # Record of board_service_room_type should contain the
        # room types properties.

        # ARRANGE
        self._create_common_scenario()
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class.id,
                "price": 25,
            }
        )
        board_service_test = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
                "pms_property_ids": [self.property1.id, self.property2.id],
            }
        )
        # ACT
        new_bsrt = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": room_type_double.id,
                "pms_board_service_id": board_service_test.id,
            }
        )
        # ASSERT
        self.assertEqual(
            new_bsrt.pms_property_ids.ids,
            room_type_double.pms_property_ids.ids,
            "Record of board_service_room_type should contain the"
            " room types properties.",
        )

    def test_create_rt_props_eq_bs_props(self):
        # TEST CASE
        # Create board service for a room type and the room type
        # have THE SAME properties than the board service.
        # Record of board_service_room_type should contain the
        # room types properties that matchs with the board
        # service properties

        # ARRANGE
        self._create_common_scenario()
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class.id,
                "price": 25,
            }
        )
        board_service_test = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
                "pms_property_ids": [self.property1.id],
            }
        )
        # ACT
        new_bsrt = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": room_type_double.id,
                "pms_board_service_id": board_service_test.id,
            }
        )
        # ASSERT
        self.assertTrue(
            new_bsrt.pms_property_ids.ids == room_type_double.pms_property_ids.ids
            and new_bsrt.pms_property_ids.ids
            == board_service_test.pms_property_ids.ids,
            "Record of board_service_room_type should contain the room "
            "types properties and matchs with the board service properties",
        )

    def test_create_rt_no_props_and_bs_props(self):
        # TEST CASE
        # Create board service for a room type and the room type
        # hasn't properties but the board services.
        # Record of board_service_room_type should contain the
        # board service properties.

        # ARRANGE
        self._create_common_scenario()
        room_type_double = self.env["pms.room.type"].create(
            {
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class.id,
                "price": 25,
            }
        )
        board_service_test = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
                "pms_property_ids": [self.property1.id],
            }
        )
        # ACT
        new_bsrt = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": room_type_double.id,
                "pms_board_service_id": board_service_test.id,
            }
        )
        # ASSERT
        self.assertEqual(
            new_bsrt.pms_property_ids.ids,
            board_service_test.pms_property_ids.ids,
            "Record of board_service_room_type should contain the"
            " board service properties.",
        )

    def test_create_rt_props_and_bs_no_props(self):
        # TEST CASE
        # Create board service for a room type and the board service
        # hasn't properties but the room type.
        # Record of board_service_room_type should contain the
        # room type properties.

        # ARRANGE
        self._create_common_scenario()
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.property1.id, self.property2.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class.id,
                "price": 25,
            }
        )
        board_service_test = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
            }
        )
        # ACT
        new_bsrt = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": room_type_double.id,
                "pms_board_service_id": board_service_test.id,
            }
        )
        # ASSERT
        self.assertEqual(
            new_bsrt.pms_property_ids.ids,
            room_type_double.pms_property_ids.ids,
            "Record of board_service_room_type should contain the"
            " room type properties.",
        )

    def test_create_rt_no_props_and_bs_no_props(self):
        # TEST CASE
        # Create board service for a room type and the board service
        # has no properties and neither does the room type
        # Record of board_service_room_type shouldnt contain properties.

        # ARRANGE
        self._create_common_scenario()
        room_type_double = self.env["pms.room.type"].create(
            {
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class.id,
                "price": 25,
            }
        )
        board_service_test = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
            }
        )
        # ACT
        new_bsrt = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": room_type_double.id,
                "pms_board_service_id": board_service_test.id,
            }
        )
        # ASSERT
        self.assertFalse(
            new_bsrt.pms_property_ids.ids,
            "Record of board_service_room_type shouldnt contain properties.",
        )
