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
                            
                        },
                    )
                ],
            }
        )

        cls.so.sudo().action_confirm()

        cls.currency_usd_id = cls.env.ref("base.USD").id

        cls.env["account.move"].invalidate_cache()

        cls.account_move = cls.env["account.move"].create(
            {
                "partner_id": cls.partner.id,
                "currency_id": cls.currency_usd_id,
                "move_type": "out_invoice",
                "invoice_date": fields.Date.today(),
                #"invoice_payment_term_id": self.payment_term.id,
                "invoice_line_ids": [
                #"line_ids": [
                    [
                        0,
                        0,
                        {
                            "pms_reservation_id": cls.reservation.id,
                            "product_id": cls.product.id,
                            "quantity": 12.0,
                            "price_unit": None,
                            "name": "something",
                            #"account_id": self.account_revenue.id,
                        },
                    ],
                    [
                        0,
                        0,
                        {
                            "pms_reservation_id": cls.reservation_2.id,
                            "product_id": cls.product.id,
                            "quantity": 12.0,
                            "price_unit": None,
                            "name": "something",
                            #"account_id": self.account_revenue.id,
                        },
                    ]
                ],
            }
        )


    def test_compute_reservation_count(self):
        self.assertTrue( self.account_move.reservation_count, 2)
        print("********** Number of reservations ********** :", self.account_move.reservation_count)
        
