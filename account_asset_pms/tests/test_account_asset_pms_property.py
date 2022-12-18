# Copyright 2022 Comunitea Servicios Tecnológicos S.L. (https://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import time

from odoo.tests import common


class TestAccountAssetPmsProperty(common.TransactionCase):
    def setUp(self):
        super(TestAccountAssetPmsProperty, self).setUp()
        self.AccountAccount = self.env["account.account"]
        self.AccountAsset = self.env["account.asset"]
        self.ResUsers = self.env["res.users"]
        self.product_id = self.env["product.template"].search(
            [("type", "=", "service")], limit=1
        )
        # Groups
        self.grp_account_manager = self.env.ref("account.group_account_manager")
        self.group_user = self.env.ref("base.group_user")
        # Company
        self.company = self.env.ref("base.main_company")
        # Pricelist
        self.pricelist = self.env["product.pricelist"].create(
            {
                "name": "Pricelist",
            }
        )
        # Property
        self.pms_property = self.env["pms.property"].create(
            {
                "name": "Pms_property_test",
                "company_id": self.company.id,
                "default_pricelist_id": self.pricelist.id,
            }
        )
        # Accounts
        self.account_expense = self.AccountAccount.search(
            [
                ("company_id", "=", self.company.id),
                (
                    "user_type_id",
                    "=",
                    self.env.ref("account.data_account_type_expenses").id,
                ),
            ],
            limit=1,
        )
        self.account_asset = self.env["account.account"].search(
            [
                ("company_id", "=", self.company.id),
                (
                    "user_type_id",
                    "=",
                    self.env.ref("account.data_account_type_current_assets").id,
                ),
            ],
            limit=1,
        )
        # Journal
        self.journal_purchase = self.env["account.journal"].search(
            [("company_id", "=", self.company.id), ("type", "=", "purchase")], limit=1
        )
        # Asset Profile
        self.profile_id = self.env["account.asset.profile"].create(
            {
                "account_expense_depreciation_id": self.account_expense.id,
                "account_asset_id": self.account_asset.id,
                "account_depreciation_id": self.account_asset.id,
                "journal_id": self.journal_purchase.id,
                "name": "Hardware - 3 Years",
                "method_time": "year",
                "method_number": 3,
                "method_period": "year",
            }
        )
        self.asset1 = self._create_asset(self.pms_property)

    def _create_asset(self, pms_property):
        asset = self.AccountAsset.create(
            {
                "name": "Test Asset",
                "profile_id": self.profile_id.id,
                "purchase_value": 1000,
                "salvage_value": 0,
                "date_start": time.strftime("%Y-01-01"),
                "method_time": "year",
                "method_number": 3,
                "method_period": "month",
                "pms_property_id": pms_property.id,
            }
        )
        return asset

    def test_asset(self):
        self.assertEqual(self.asset1.pms_property_id.id, self.pms_property.id)
