# Copyright (c) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import date, timedelta

from odoo.tests import SavepointCase


class TestAccountMove(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env.ref("pms_sale.product_product_reservation")
        cls.partner_owner = cls.env["res.partner"].create({"name": "Property Owner"})
        cls.partner_property = cls.env["res.partner"].create({"name": "Property"})
        cls.property = cls.env["pms.property"].create(
            {"owner_id": cls.partner_owner.id, "partner_id": cls.partner_property.id}
        )
        cls.reservation = cls.env["pms.reservation"].create(
            {"name": "Test Reservation", "property_id": cls.property.id}
        )
        cls.sale_order_obj = cls.env["sale.order"]
        cls.partner = cls.env["res.partner"].create({"name": "TEST CUSTOMER"})
        cls.sale_pricelist = cls.env["product.pricelist"].create(
            {"name": "Test Pricelist", "currency_id": cls.env.ref("base.USD").id}
        )
        cls.so = cls.sale_order_obj.create(
            {
                "partner_id": cls.partner.id,
                "date_order": date.today() + timedelta(days=1),
                "pricelist_id": cls.sale_pricelist.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": cls.reservation.name,
                            "product_id": cls.product.id,
                            "product_uom_qty": 5.0,
                            "product_uom": cls.product.uom_po_id.id,
                            "price_unit": 10.0,
                            "qty_delivered": 1,
                            "pms_reservation_id": cls.reservation.id,
                            "property_id": cls.reservation.property_id.id,
                        },
                    ),
                ],
            }
        )

    def test_compute_reservation_count(self):
        self.so.sudo().action_confirm()
        invoice = self.so._create_invoices()
        self.assertEqual(invoice.reservation_count, 1)
