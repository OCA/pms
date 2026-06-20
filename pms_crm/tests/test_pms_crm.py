# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.pms_base.tests.common import PmsBaseCase


class TestPmsCrm(PmsBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lead = cls.env["crm.lead"].create({"name": "Test Lead"})
        cls.lead2 = cls.env["crm.lead"].create({"name": "Second Lead"})
        cls.property2 = cls.env["pms.property"].create(
            {
                "name": "Second Property",
                "owner_id": cls.owner.id,
                "tz": "UTC",
                "team_id": cls.team.id,
            }
        )

    def test_lead_property_link(self):
        """Linking from the lead updates the inverse on the property."""
        self.lead.property_ids = [(4, self.property.id)]
        self.assertIn(self.property, self.lead.property_ids)
        self.assertIn(self.lead, self.property.lead_ids)
        self.assertEqual(self.property.lead_count, 1)

    def test_lead_property_count(self):
        """property_count reflects linked properties on the lead."""
        self.lead.property_ids = [(6, 0, [self.property.id, self.property2.id])]
        self.assertEqual(self.lead.property_count, 2)

    def test_property_lead_count(self):
        """lead_count reflects linked leads on the property."""
        self.property.lead_ids = [(6, 0, [self.lead.id, self.lead2.id])]
        self.assertEqual(self.property.lead_count, 2)

    def test_action_view_properties_single(self):
        """action_view_properties opens the property form for one record."""
        self.lead.property_ids = [(4, self.property.id)]
        action = self.lead.action_view_properties()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "pms.property")
        self.assertEqual(action["res_id"], self.property.id)

    def test_action_view_properties_multiple(self):
        """action_view_properties filters the list for several properties."""
        self.lead.property_ids = [(6, 0, [self.property.id, self.property2.id])]
        action = self.lead.action_view_properties()
        self.assertEqual(action["domain"], [("id", "in", self.lead.property_ids.ids)])

    def test_action_view_leads_single(self):
        """action_view_leads opens the lead form for one record."""
        self.property.lead_ids = [(4, self.lead.id)]
        action = self.property.action_view_leads()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "crm.lead")
        self.assertEqual(action["res_id"], self.lead.id)

    def test_action_view_leads_multiple(self):
        """action_view_leads filters the list for several leads."""
        self.property.lead_ids = [(6, 0, [self.lead.id, self.lead2.id])]
        action = self.property.action_view_leads()
        self.assertEqual(action["domain"], [("id", "in", self.property.lead_ids.ids)])
