# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class TestPmsCrm(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.property = cls.env["pms.property"].create({"name": "Test Property"})
        cls.lead = cls.env["crm.lead"].create({"name": "Test Lead"})

    def test_lead_property_link(self):
        """Test bidirectional link between leads and properties."""
        self.lead.property_ids = [(4, self.property.id)]
        self.assertIn(self.property, self.lead.property_ids)
        self.assertEqual(self.property.lead_count, 1)

    def test_property_lead_count(self):
        """Test that lead count reflects linked leads."""
        self.lead.property_ids = [(4, self.property.id)]
        self.property._compute_lead_count()
        self.assertEqual(self.property.lead_count, 1)

    def test_action_view_leads(self):
        """Test action_view_leads returns a valid window action."""
        self.lead.property_ids = [(4, self.property.id)]
        action = self.property.action_view_leads()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "crm.lead")
