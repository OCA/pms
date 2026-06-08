# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command

from odoo.addons.pms_base.tests.common import PmsBaseCase


class TestPmsContract(PmsBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env["res.partner"].create({"name": "Test Vendor"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test Service", "type": "service", "list_price": 100.0}
        )
        cls.property2 = cls.env["pms.property"].create(
            {
                "name": "Second Property",
                "owner_id": cls.owner.id,
                "tz": "UTC",
                "team_id": cls.team.id,
            }
        )

    def _create_contract(self, name="Test Contract", property_rec=None):
        property_rec = property_rec or self.property
        return self.env["contract.contract"].create(
            {
                "name": name,
                "partner_id": self.vendor.id,
                "contract_type": "purchase",
                "contract_line_ids": [
                    Command.create(
                        {
                            "name": "Contract Line",
                            "product_id": self.product.id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "date_start": "2024-01-01",
                            "recurring_next_date": "2024-01-01",
                            "recurring_rule_type": "monthly",
                            "property_id": property_rec.id,
                        }
                    )
                ],
            }
        )

    def _create_service(self, contract):
        return self.env["pms.service"].create(
            {
                "name": self.product.id,
                "property_id": self.property.id,
                "vendor_id": self.vendor.id,
                "contract_id": contract.id,
            }
        )

    def test_contract_count_initial(self):
        self.assertEqual(self.property.contract_count, 0)

    def test_action_view_contracts_empty(self):
        action = self.property.action_view_contracts()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "contract.contract")

    def test_contract_count_with_service(self):
        contract = self._create_contract()
        self._create_service(contract)
        self.assertEqual(self.property.contract_count, 1)
        self.assertIn(contract, self.property.contract_ids)

    def test_action_view_contracts_single(self):
        contract = self._create_contract()
        self._create_service(contract)
        action = self.property.action_view_contracts()
        self.assertEqual(action["res_id"], contract.id)
        self.assertEqual(action["views"][0][1], "form")

    def test_action_view_contracts_multiple(self):
        contract1 = self._create_contract(name="Contract 1")
        contract2 = self._create_contract(name="Contract 2")
        self.env["pms.service"].create(
            [
                {
                    "name": self.product.id,
                    "property_id": self.property.id,
                    "vendor_id": self.vendor.id,
                    "contract_id": contract1.id,
                },
                {
                    "name": self.product.id,
                    "property_id": self.property.id,
                    "vendor_id": self.vendor.id,
                    "contract_id": contract2.id,
                },
            ]
        )
        action = self.property.action_view_contracts()
        self.assertEqual(set(action["domain"][0][2]), {contract1.id, contract2.id})

    def test_contract_property_count(self):
        contract = self._create_contract()
        self.assertEqual(contract.property_count, 1)
        self.assertIn(self.property, contract.property_ids)

    def test_contract_property_count_multiple(self):
        contract = self.env["contract.contract"].create(
            {
                "name": "Multi Property Contract",
                "partner_id": self.vendor.id,
                "contract_type": "purchase",
                "contract_line_ids": [
                    Command.create(
                        {
                            "name": "Line 1",
                            "product_id": self.product.id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "date_start": "2024-01-01",
                            "recurring_next_date": "2024-01-01",
                            "recurring_rule_type": "monthly",
                            "property_id": self.property.id,
                        }
                    ),
                    Command.create(
                        {
                            "name": "Line 2",
                            "product_id": self.product.id,
                            "quantity": 1.0,
                            "price_unit": 50.0,
                            "date_start": "2024-01-01",
                            "recurring_next_date": "2024-01-01",
                            "recurring_rule_type": "monthly",
                            "property_id": self.property2.id,
                        }
                    ),
                ],
            }
        )
        self.assertEqual(contract.property_count, 2)

    def test_action_view_properties_empty(self):
        contract = self.env["contract.contract"].create(
            {
                "name": "Empty Contract",
                "partner_id": self.vendor.id,
                "contract_type": "purchase",
            }
        )
        action = contract.action_view_properties()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "pms.property")

    def test_action_view_properties_single(self):
        contract = self._create_contract()
        action = contract.action_view_properties()
        self.assertEqual(action["res_id"], self.property.id)
        self.assertEqual(action["views"][0][1], "form")

    def test_action_view_properties_multiple(self):
        contract = self.env["contract.contract"].create(
            {
                "name": "Multi Property Contract",
                "partner_id": self.vendor.id,
                "contract_type": "purchase",
                "contract_line_ids": [
                    Command.create(
                        {
                            "name": "Line 1",
                            "product_id": self.product.id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "date_start": "2024-01-01",
                            "recurring_next_date": "2024-01-01",
                            "recurring_rule_type": "monthly",
                            "property_id": self.property.id,
                        }
                    ),
                    Command.create(
                        {
                            "name": "Line 2",
                            "product_id": self.product.id,
                            "quantity": 1.0,
                            "price_unit": 50.0,
                            "date_start": "2024-01-01",
                            "recurring_next_date": "2024-01-01",
                            "recurring_rule_type": "monthly",
                            "property_id": self.property2.id,
                        }
                    ),
                ],
            }
        )
        action = contract.action_view_properties()
        self.assertEqual(
            set(action["domain"][0][2]), {self.property.id, self.property2.id}
        )

    def test_prepare_invoice_line_with_property(self):
        contract = self._create_contract()
        line = contract.contract_line_ids
        vals = line._prepare_invoice_line()
        self.assertEqual(vals["property_ids"], [(6, 0, self.property.ids)])

    def test_prepare_invoice_line_without_property(self):
        contract = self.env["contract.contract"].create(
            {
                "name": "No Property Contract",
                "partner_id": self.vendor.id,
                "contract_type": "purchase",
                "contract_line_ids": [
                    Command.create(
                        {
                            "name": "Line Without Property",
                            "product_id": self.product.id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "date_start": "2024-01-01",
                            "recurring_next_date": "2024-01-01",
                            "recurring_rule_type": "monthly",
                        }
                    )
                ],
            }
        )
        vals = contract.contract_line_ids._prepare_invoice_line()
        self.assertNotIn("property_ids", vals)

    def test_module_models_import(self):
        from .. import models as pms_contract_models

        self.assertTrue(pms_contract_models)
