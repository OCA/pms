from odoo.exceptions import UserError
from odoo.tests import common


class TestPmsBoardService(common.SavepointCase):
    def test_property_integrity(self):
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
        self.product = self.env["product.product"].create(
            {"name": "Product", "pms_property_ids": self.property1}
        )

        self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Board Service",
                "default_code": "CB",
            }
        )
        with self.assertRaises(UserError):
            board_service_line = self.board_service_line = self.env[
                "pms.board.service.line"
            ].create(
                {
                    "product_id": self.product.id,
                    "pms_board_service_id": self.board_service.id,
                }
            )
            board_service_line.pms_property_ids = [self.property2.id]
