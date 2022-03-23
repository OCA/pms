from odoo.tests.common import TransactionCase
from odoo import fields
from odoo.tests import SavepointCase
from odoo import api

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

        # MODELS
        cls.AccountMove = cls.env["account.move"]
        cls.ResPartner = cls.env["res.partner"]
        cls.AccountAccount = cls.env["account.account"]
        cls.AccountJournal = cls.env["account.journal"]

        # INSTANCE
        partners = cls.ResPartner.search(
            [("type", "!=", "invoice"), ("child_ids", "=", False)], limit=2
        )
        cls.partner = partners[0]
        cls.partner_2 = partners[1]

        # invoice
        journal = cls.AccountJournal.create(
            {"name": "Purchase Journal - Test", "code": "STPJ", "type": "purchase"}
        )
        invoice_vals = {
            "name": "TEST",
            "move_type": "in_invoice",
            "partner_id": cls.partner.id,
            "journal_id": journal.id,

            "line_ids":  [(0, 0, {})],
        }
        #cls.invoice = cls.AccountMove.create(invoice_vals)
        cls.account_move = cls.AccountMove.create(invoice_vals)

        print("///////////////////////////////////////", cls.account_move.reservation_count)

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



    @api.depends("line_ids")
    def test_compute_reservation_count(self):
        self.account_move._compute_reservation_count() 

        #total_len = self.account_move.search_count(['id', '=', '99'])
        #print("total length", total_len)
        #for r in self.account_move:
            #print("reservation_count:", r.reservation_count)


        #for invoice in self:
            #reservation = invoice.line_ids.mapped("pms_reservation_id")
            #invoice.reservation_count = len(reservation)
            #self.assertEqual(invoice.reservation_count, 3)

    #def test_action_view_reservation_list(self):
        #print(self.account_move.action_view_reservation_list())

