from .common import TestPms


class TestPmsBoardServiceRoomType(TestPms):
    def test_create_rt_props_gt_bs_props(self):
        """
        Create board service for a room type and the room type
        have MORE properties than the board service.
        Record of board_service_room_type should contain the
        board service properties.
        """
        # ARRANGE
        pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )

        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id, pms_property2.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
                "price": 25,
            }
        )
        board_service_test = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
                "pms_property_ids": [self.pms_property1.id],
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
        """
        Create board service for a room type and the room type
        have LESS properties than the board service.
        Record of board_service_room_type should contain the
        room types properties.
        """
        # ARRANGE
        pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
                "price": 25,
            }
        )
        board_service_test = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
                "pms_property_ids": [self.pms_property1.id, pms_property2.id],
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
        """
        Create board service for a room type and the room type
        have THE SAME properties than the board service.
        Record of board_service_room_type should contain the
        room types properties that matchs with the board
        service properties
        """
        # ARRANGE
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
                "price": 25,
            }
        )
        board_service_test = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
                "pms_property_ids": [self.pms_property1.id],
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
        """
        Create board service for a room type and the room type
        hasn't properties but the board services.
        Record of board_service_room_type should contain the
        board service properties.
        """
        # ARRANGE
        room_type_double = self.env["pms.room.type"].create(
            {
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
                "price": 25,
            }
        )
        board_service_test = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
                "pms_property_ids": [self.pms_property1.id],
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
        """
        Create board service for a room type and the board service
        hasn't properties but the room type.
        Record of board_service_room_type should contain the
        room type properties.
        """
        # ARRANGE
        pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id, pms_property2.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
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
        """
        Create board service for a room type and the board service
        has no properties and neither does the room type
        Record of board_service_room_type shouldnt contain properties.
        """
        # ARRANGE

        room_type_double = self.env["pms.room.type"].create(
            {
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
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
