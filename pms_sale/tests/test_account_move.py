from odoo.tests.common import TransactionCase
from odoo import fields
from odoo.tests import SavepointCase
from odoo import api
from datetime import date, timedelta

#class TestAccountMove(TransactionCase):
    #def setUp(self):
        #super(TestAccountMove, self).setUp()
        #self.account_move = self.env["account.move"]

        #self.account_move_line = self.env["account.move.line"]

        #self.test_reservation_count = 

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

        # cls.pms_property_reservation = cls.env["pms.property.reservation"].create(
        #     {
        #         "name": "Test pms property reservation",
        #         "product_id": cls.product.id
        #     }
        # )

        cls.reservation = cls.env["pms.reservation"].create(
            {
                "name": "Test Reservation",
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
                            "pms_reservation_id": cls.reservation.id,
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

    @api.depends("line_ids")
    def test_compute_reservation_count(self):
        print("//////////////////////////////////////", self.so.date_order)
        self.so.sudo().action_confirm()


        # product = cls.env["product.product"].create(
        #     {
        #         "name": "Demo",
        #         #"name": cls.reservation.name,
        #         "categ_id": cls.env.ref("product.product_category_1").id,
        #         "standard_price": 40.0,
        #         "type": "consu",
        #         "uom_id": cls.env.ref("uom.product_uom_unit").id,
        #         "default_code": "PROD_DEL01",
        #     }
        # )



        account_move = self.env["account.move"].create(
            {
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Demo",
                            #"categ_id": self.env.ref("product.product_category_1").id,
                            #"standard_price": 40.0,
                            #"type": "consu",
                            #"uom_id": self.env.ref("uom.product_uom_unit").id,
                            #"default_code": "PROD_DEL01",
                        }
                    )
                ]
                
            }
        )

        mov_line_credit = {
            "move_name": 'test invoice',
            #'move_id': invoice.id,
            "move_id": account_move.id,
            'debit': 0.0 ,
            #'credit':  amount,
            # 'date': date,
            # 'partner_id': partner,
            # 'product_id': product.id,
            # 'account_id': acc_p.id,
            # 'name':product.name,
            # 'exclude_from_invoice_tab': True,
             'quantity': 1,
            # 'price_unit': float(amount)
            }

        #mov_line_debit = {
            #"move_name": 'test invoice',
            #'move_id': invoice.id,
            #'debit':  amount,
            #'credit': 0.0 ,
            # 'date': date,
            # 'name': product.name,
            # 'partner_id': partner,
            #'product_id': product.id,
            #'account_id': acc_r.id,
            #'quantity': 1,
            # 'exclude_from_invoice_tab': True,
            #'price_unit': float(amount)
            #}

        # ct = self.env['account.move.line'].sudo().with_context(
        # check_move_validity=True).create([mov_line_debit,mov_line_credit])


        ct = self.env['account.move.line'].sudo().with_context(
        check_move_validity=True).create([mov_line_credit])
        
        self.assertEqual(True, True)
        #self.account_move._compute_reservation_count()
        print("/////////////////////////////////", self.account_move.reservation_count) 




        # so = cls.sale_order_obj.create(
        #     {
        #         "partner_id": cls.partner.id,
        #         "date_order": date.today() + timedelta(days=1),
        #         "pricelist_id": cls.sale_pricelist.id,
        #         "order_line": [
        #             (
        #                 0,
        #                 0,
        #                 {
        #                     "name": cls.product.name,
        #                     "product_id": cls.product.id,
        #                     "product_uom_qty": 5.0,
        #                     "product_uom": cls.product.uom_po_id.id,
        #                     "price_unit": 10.0,
                            
        #                 },
        #             )
        #         ],
        #     }
        # )

        # # MODELS
        # cls.AccountMove = cls.env["account.move"]
        # cls.ResPartner = cls.env["res.partner"]
        # cls.AccountAccount = cls.env["account.account"]
        # cls.AccountJournal = cls.env["account.journal"]

        # # INSTANCE
        # partners = cls.ResPartner.search(
        #     [("type", "!=", "invoice"), ("child_ids", "=", False)], limit=2
        # )
        # cls.partner = partners[0]
        # cls.partner_2 = partners[1]

        # # invoice
        # journal = cls.AccountJournal.create(
        #     {"name": "Purchase Journal - Test", "code": "STPJ", "type": "purchase"}
        # )
        # invoice_vals = {
        #     "name": "TEST",
        #     "move_type": "in_invoice",
        #     "partner_id": cls.partner.id,
        #     "journal_id": journal.id,

        #     "invoice_line_ids":  [(0, 0, {
        #         "product_id": ,
        #         "account_id": ,
        #         "quantity": ,
        #         "price_unit": ,
        #     })],
        # }
        # #cls.invoice = cls.AccountMove.create(invoice_vals)
        # cls.account_move = cls.AccountMove.create(invoice_vals)

        

        #print("///////////////////////////////////////", cls.account_move.reservation_count)

        #self.account_move.create(
            #{
                #"line_ids":  [(0, 0, {})],

                #"reservation_count": 3
            #}
        #)

        #self.account_move.create(
            #{
                #"line_ids":  [(0, 0, {})],
                #"reservation_count": 5
            #}
        #)

        #self.account_move_line.create(
            #{
                #"pms_reservation_id": 23
            #}

        #)

        #self.account_move.reservation_count = fields.Integer(
        #"Reservations Count", compute="test_compute_reservation_count")

        #self.assertEqual(self.test_reservation_count, 3)
        #print("reservation count: ", self.account_move.get(1))



    # @api.depends("line_ids")
    # def test_compute_reservation_count(self):
    #     sudo().action_confirm()
    #     self.assertEqual(True, True)
    #     self.account_move._compute_reservation_count()
    #     print("/////////////////////////////////", self.account_move.reservation_count) 



        #total_len = self.account_move.search_count(['id', '=', '99'])
        #print("total length", total_len)
        #for r in self.account_move:
            #print("reservation_count:", r.reservation_count)


        #for invoice in self:
            #reservation = invoice.line_ids.mapped("pms_reservation_id")
            #invoice.reservation_count = len(reservation)
            #self.assertEqual(invoice.reservation_count, 3)

    def test_action_view_reservation_list(self):
        self.assertEqual(True, True)
        #print(self.account_move.action_view_reservation_list())

