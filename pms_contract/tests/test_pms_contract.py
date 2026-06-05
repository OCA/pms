# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class TestPmsContract(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.property = cls.env["pms.property"].create({"name": "Test Property"})
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})

    def test_contract_count_initial(self):
        self.assertEqual(self.property.contract_count, 0)

    def test_action_view_contracts(self):
        action = self.property.action_view_contracts()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "contract.contract")
