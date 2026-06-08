# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class TestAccountMove(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not cls.env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", cls.env.company.id)]
        ):
            cls.env["account.chart.template"].try_loading(
                "generic_coa", company=cls.env.company
            )
        cls.product = cls.env.ref("pms_sale.product_product_reservation")
        cls.partner = cls.env["res.partner"].create({"name": "TEST CUSTOMER"})
        cls.property = (
            cls.env["pms.property"]
            .sudo()
            .create(
                {
                    "name": "Test Property",
                    "owner_id": cls.partner.id,
                }
            )
        )
        cls.reservation = (
            cls.env["pms.reservation"]
            .sudo()
            .create({"name": "Test Reservation", "property_id": cls.property.id})
        )

    def test_compute_reservation_count(self):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.reservation.name,
                            "product_id": self.product.id,
                            "quantity": 1.0,
                            "price_unit": 10.0,
                            "pms_reservation_id": self.reservation.id,
                        },
                    )
                ],
            }
        )
        self.assertEqual(invoice.reservation_count, 1)
