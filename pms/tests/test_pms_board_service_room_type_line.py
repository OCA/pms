from odoo.exceptions import UserError

from .common import TestPms


class TestPmsBoardServiceRoomTypeLine(TestPms):
    def test_pms_bsrtl_product_property_integrity(self):
        """
        Creation of a board service room type line without property, of a product
        only available for a specific property.
        """
        # ARRANGE

        product = self.env["product.product"].create(
            {"name": "Product", "pms_property_ids": self.pms_property1}
        )
        board_service = self.env["pms.board.service"].create(
            {
                "name": "Board Service",
                "default_code": "CB",
            }
        )
        room_type = self.env["pms.room.type"].create(
            {
                "name": "Room Type",
                "default_code": "Type1",
                "class_id": self.room_type_class1.id,
            }
        )
        board_service_room_type = self.env["pms.board.service.room.type"].create(
            {
                "pms_board_service_id": board_service.id,
                "pms_room_type_id": room_type.id,
            }
        )

        # ACT & ASSERT
        with self.assertRaises(
            UserError, msg="Board service room type line shouldnt be created."
        ):
            self.env["pms.board.service.room.type.line"].create(
                {
                    "pms_board_service_room_type_id": board_service_room_type.id,
                    "product_id": product.id,
                }
            )

    def test_pms_bsrtl_board_service_line_prop_integrity(self):
        """
        Creation of a board service room type line with a specific property,
        of board service without property.
        """
        # ARRANGE
        pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 1",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        product = self.env["product.product"].create(
            {"name": "Product", "pms_property_ids": [self.pms_property1.id]}
        )
        board_service = self.env["pms.board.service"].create(
            {
                "name": "Board Service",
                "default_code": "CB",
            }
        )

        room_type = self.env["pms.room.type"].create(
            {
                "name": "Room Type",
                "default_code": "Type1",
                "class_id": self.room_type_class1.id,
            }
        )
        board_service_room_type = self.env["pms.board.service.room.type"].create(
            {
                "pms_board_service_id": board_service.id,
                "pms_room_type_id": room_type.id,
            }
        )

        # ACT & ASSERT
        with self.assertRaises(
            UserError, msg="Board service line shouldnt be created."
        ):
            self.env["pms.board.service.room.type.line"].create(
                {
                    "product_id": product.id,
                    "pms_property_ids": [pms_property2.id],
                    "pms_board_service_room_type_id": board_service_room_type.id,
                }
            )
