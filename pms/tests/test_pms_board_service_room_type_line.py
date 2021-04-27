from odoo.exceptions import UserError
from odoo.tests import common


class TestPmsBoardServiceRoomTypeLine(common.SavepointCase):
    def test_check_product_property_integrity(self):
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
        self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Board Service",
                "default_code": "CB",
                "pms_property_ids": self.property1,
            }
        )
        self.room_type_class = self.env["pms.room.type.class"].create(
            {
                "name": "Room Type Class",
                "default_code": "SIN1",
                "pms_property_ids": self.property1,
            }
        )
        self.room_type = self.env["pms.room.type"].create(
            {
                "name": "Room Type",
                "default_code": "Type1",
                "pms_property_ids": self.property1,
                "class_id": self.room_type_class.id,
            }
        )
        self.board_service_room_type = self.env["pms.board.service.room.type"].create(
            {
                "pms_board_service_id": self.board_service.id,
                "pms_room_type_id": self.room_type.id,
                "pms_property_ids": self.property1,
            }
        )

        self.product = self.env["product.product"].create(
            {"name": "Product", "pms_property_ids": self.property2}
        )
        with self.assertRaises(UserError):
            self.env["pms.board.service.room.type.line"].create(
                {
                    "pms_board_service_room_type_id": self.board_service_room_type.id,
                    "product_id": self.product.id,
                }
            )
