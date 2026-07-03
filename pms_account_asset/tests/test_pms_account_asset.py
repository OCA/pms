# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class TestPmsAccountAsset(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        pms_manager = cls.env.ref("pms_base.group_pms_manager")
        cls.env.user.write({"group_ids": [Command.link(pms_manager.id)]})
        cls.owner = cls.env["res.partner"].create({"name": "Test Owner"})
        cls.team = cls.env.ref("pms_base.pms_team_default")
        cls.property = cls.env["pms.property"].create(
            {
                "name": "Test Property",
                "owner_id": cls.owner.id,
                "tz": "UTC",
                "team_id": cls.team.id,
            }
        )
        cls.property2 = cls.env["pms.property"].create(
            {
                "name": "Second Property",
                "owner_id": cls.owner.id,
                "tz": "UTC",
                "team_id": cls.team.id,
            }
        )
        cls.profile = cls.env["account.asset.profile"].create(
            {
                "account_expense_depreciation_id": cls.company_data[
                    "default_account_expense"
                ].id,
                "account_asset_id": cls.company_data["default_account_assets"].id,
                "account_depreciation_id": cls.company_data[
                    "default_account_assets"
                ].id,
                "journal_id": cls.company_data["default_journal_purchase"].id,
                "name": "Test Asset Profile",
            }
        )

    def _create_asset(self, name="Test Asset", property_rec=None):
        property_rec = property_rec or self.property
        return self.env["account.asset"].create(
            {
                "name": name,
                "profile_id": self.profile.id,
                "purchase_value": 1000.0,
                "date_start": "2024-01-01",
                "property_id": property_rec.id,
            }
        )

    def test_asset_count_initial(self):
        self.assertEqual(self.property.asset_count, 0)
        self.assertFalse(self.property.asset_ids)

    def test_action_view_assets_empty(self):
        action = self.property.action_view_assets()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "account.asset")

    def test_account_asset_property_link(self):
        asset = self._create_asset()
        self.assertEqual(asset.property_id, self.property)
        self.assertIn(asset, self.property.asset_ids)

    def test_asset_count_with_assets(self):
        self._create_asset()
        self.assertEqual(self.property.asset_count, 1)

    def test_compute_asset_count_multiple_properties(self):
        self._create_asset()
        self._create_asset(name="Other Asset", property_rec=self.property2)
        self.assertEqual(self.property.asset_count, 1)
        self.assertEqual(self.property2.asset_count, 1)

    def test_action_view_assets_single(self):
        asset = self._create_asset()
        action = self.property.action_view_assets()
        self.assertEqual(action["res_id"], asset.id)
        self.assertEqual(action["views"][0][1], "form")

    def test_action_view_assets_multiple(self):
        assets = self.env["account.asset"].create(
            [
                {
                    "name": "Asset 1",
                    "profile_id": self.profile.id,
                    "purchase_value": 100.0,
                    "date_start": "2024-01-01",
                    "property_id": self.property.id,
                },
                {
                    "name": "Asset 2",
                    "profile_id": self.profile.id,
                    "purchase_value": 200.0,
                    "date_start": "2024-01-01",
                    "property_id": self.property.id,
                },
            ]
        )
        action = self.property.action_view_assets()
        self.assertEqual(action["domain"], [("id", "in", assets.ids)])

    def test_module_models_import(self):
        from .. import models as pms_account_asset_models
        from ..models import account_asset, pms_property

        self.assertTrue(pms_account_asset_models)
        self.assertTrue(account_asset.AccountAsset)
        self.assertTrue(pms_property.PmsProperty)
        self.assertIn("property_id", self.env["account.asset"]._fields)
        self.assertIn("asset_ids", self.env["pms.property"]._fields)
