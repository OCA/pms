from odoo.tests.common import TransactionCase
from odoo import fields
from odoo.tests import SavepointCase
from odoo import api
from datetime import date, timedelta


class TestAccountMove(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product = cls.env["product.product"].create(
            {
                "name": "Demo",
                "categ_id": cls.env.ref("product.product_category_1").id,
                "standard_price": 40.0,
                "type": "consu",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "default_code": "PROD_DEL01",
            }
        )

        cls.partner_owner = cls.env["res.partner"].create({"name": "Property Owner"})

        cls.partner_property = cls.env["res.partner"].create({"name": "Property"})

        cls.property = cls.env["pms.property"].create(
            {
                "owner_id": cls.partner_owner.id,
                "partner_id": cls.partner_property.id
            }
        )

        cls.reservation = cls.env["pms.reservation"].create(
            {
                "name": "Test Reservation",
                "property_id": cls.property.id
                
            }
        )
        
        cls.reservation_2 = cls.env["pms.reservation"].create(
            {
                "name": "Test Reservation 2",
                "property_id": cls.property.id
                
            }
        )

        cls.reservation_3 = cls.env["pms.reservation"].create(
            {
                "name": "Test Reservation 3",
                "property_id": cls.property.id
                
            }
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
                            "pms_reservation_id": cls.reservation.id
                        },
                    ),
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
                            "pms_reservation_id": cls.reservation_2.id
                        },
                    ),
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
                            "pms_reservation_id": cls.reservation_3.id
                        },
                    )
                ],
            }
        )

        cls.so.sudo().action_confirm()

        cls.currency_usd_id = cls.env.ref("base.USD").id

        cls.invoice_lines = []

        #Make invoice from sale order

        for line in cls.so.order_line:
            vals = {
                'name': line.name,
                'price_unit': line.price_unit,
                'quantity': line.product_uom_qty,
                'product_id': line.product_id.id,
                'product_uom_id': line.product_uom.id,
                'tax_ids': [(6, 0, line.tax_id.ids)],
                'sale_line_ids': [(6, 0, [line.id])],
                'pms_reservation_id':  line.pms_reservation_id
            }
            cls.invoice_lines.append((0, 0, vals))

        cls.account_move = cls.env['account.move'].create({
            "partner_id": cls.partner.id,
            "currency_id": cls.currency_usd_id,
            "move_type": "out_invoice",
            "invoice_date": fields.Date.today(),
            'invoice_line_ids': cls.invoice_lines
        })


    def test_compute_reservation_count(self):
        print("********** Number of reservations in sale order ********** : ", self.account_move.reservation_count)
        self.assertEqual( self.account_move.reservation_count, 3)
        
