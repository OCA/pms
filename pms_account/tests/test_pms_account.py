# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class TestPmsAccount(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.property = cls.env["pms.property"].create({"name": "Test Property"})

    def test_invoice_count_initial(self):
        self.assertEqual(self.property.invoice_count, 0)
        self.assertEqual(self.property.bill_count, 0)

    def test_action_view_invoices(self):
        action = self.property.action_view_invoices()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "account.move")
