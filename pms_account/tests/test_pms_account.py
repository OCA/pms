# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from unittest.mock import patch

from odoo import Command

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.pms_base.tests.common import PmsBaseCase


class TestPmsAccountAnalytic(PmsBaseCase):
    """At-install tests for analytic account integration."""

    def test_property_creates_analytic_account(self):
        self.assertTrue(self.property.analytic_id)
        self.assertEqual(self.property.analytic_id.name, self.property.name)

    def test_analytic_account_linked_to_property(self):
        self.assertEqual(self.property.analytic_id.property_id, self.property)

    def test_module_models_import(self):
        from .. import models as pms_account_models

        self.assertTrue(pms_account_models)

    def test_write_property_name_and_ref(self):
        self.property.write({"name": "Renamed Property", "ref": "PROP-REF"})
        self.assertEqual(self.property.analytic_id.name, "Renamed Property")
        self.assertEqual(self.property.analytic_id.code, "PROP-REF")

    def test_write_property_updates_analytic_name(self):
        self.property.name = "Renamed Property"
        self.assertEqual(self.property.analytic_id.name, "Renamed Property")

    def test_write_property_updates_analytic_code(self):
        self.property.ref = "PROP-001"
        self.assertEqual(self.property.analytic_id.code, "PROP-001")

    def test_write_unrelated_field_does_not_sync_analytic(self):
        analytic_name = self.property.analytic_id.name
        self.property.floors_num = 3
        self.assertEqual(self.property.analytic_id.name, analytic_name)

    def test_write_creates_analytic_when_missing(self):
        self.property.analytic_id = False
        self.property.name = "Property Without Analytic"
        self.assertTrue(self.property.analytic_id)
        self.assertEqual(self.property.analytic_id.name, "Property Without Analytic")

    def test_create_property_with_existing_analytic_id(self):
        analytic = self.property.analytic_id.copy(
            {"name": "Existing Analytic", "property_id": False}
        )
        prop = self.env["pms.property"].create(
            {
                "name": "Property With Analytic",
                "owner_id": self.owner.id,
                "tz": "UTC",
                "team_id": self.team.id,
                "analytic_id": analytic.id,
            }
        )
        self.assertEqual(prop.analytic_id, analytic)

    def test_create_batch_mixed_analytic(self):
        analytic = self.property.analytic_id.copy(
            {"name": "Batch Analytic", "property_id": False}
        )
        props = self.env["pms.property"].create(
            [
                {
                    "name": "Batch With Analytic",
                    "owner_id": self.owner.id,
                    "tz": "UTC",
                    "team_id": self.team.id,
                    "analytic_id": analytic.id,
                },
                {
                    "name": "Batch Without Analytic",
                    "owner_id": self.owner.id,
                    "tz": "UTC",
                    "team_id": self.team.id,
                },
            ]
        )
        self.assertEqual(props[0].analytic_id, analytic)
        self.assertTrue(props[1].analytic_id)

    def test_create_analytic_account_without_plan(self):
        prop = self.property
        prop.analytic_id = False
        with patch.object(
            type(prop.env),
            "ref",
            return_value=prop.env["account.analytic.plan"],
        ):
            prop._create_analytic_account()
        self.assertFalse(prop.analytic_id)

    def test_invoice_count_initial(self):
        self.assertEqual(self.property.invoice_count, 0)
        self.assertEqual(self.property.bill_count, 0)

    def test_action_view_invoices_empty(self):
        action = self.property.action_view_invoices()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "account.move")
        self.assertFalse(action.get("res_id"))

    def test_action_view_bills_empty(self):
        action = self.property.action_view_bills()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "account.move")
        self.assertFalse(action.get("res_id"))


class TestPmsAccountInvoice(AccountTestInvoicingCommon):
    """Tests requiring invoices and the accounting chart of accounts."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not cls.env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", cls.env.company.id)]
        ):
            cls.env["account.chart.template"].try_loading(
                "generic_coa", company=cls.env.company
            )
        pms_manager = cls.env.ref("pms_base.group_pms_manager")
        cls.env.user.write({"group_ids": [Command.link(pms_manager.id)]})
        cls.owner = cls.env["res.partner"].create(
            {"name": "Test Owner", "email": "owner@test.com"}
        )
        cls.team = cls.env.ref("pms_base.pms_team_default")
        cls.property = cls.env["pms.property"].create(
            {
                "name": "Test Property",
                "owner_id": cls.owner.id,
                "tz": "UTC",
                "team_id": cls.team.id,
            }
        )
        cls.customer = cls.env["res.partner"].create({"name": "Test Customer"})
        cls.vendor = cls.env["res.partner"].create(
            {"name": "Test Vendor", "supplier_rank": 1}
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Service",
                "type": "service",
                "list_price": 100.0,
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

    def _create_move(self, move_type, partner):
        return self._create_invoice_one_line(
            move_type=move_type,
            partner_id=partner.id,
            product_id=self.product.id,
        )

    def _link_move_lines(self, move, *properties):
        lines = move.invoice_line_ids
        for prop in properties:
            prop.invoice_line_ids = [(4, line.id) for line in lines]

    def test_invoice_count_with_out_invoice(self):
        move = self._create_move("out_invoice", self.customer)
        self._link_move_lines(move, self.property)
        self.assertEqual(self.property.invoice_count, 1)
        self.assertIn(move, self.property.invoice_ids)
        self.assertEqual(self.property.bill_count, 0)

    def test_bill_count_with_in_invoice(self):
        move = self._create_move("in_invoice", self.vendor)
        self._link_move_lines(move, self.property)
        self.assertEqual(self.property.bill_count, 1)
        self.assertIn(move, self.property.bill_ids)
        self.assertEqual(self.property.invoice_count, 0)

    def test_invoice_count_includes_refunds(self):
        invoice = self._create_move("out_invoice", self.customer)
        refund = self._create_move("out_refund", self.customer)
        bill = self._create_move("in_invoice", self.vendor)
        credit = self._create_move("in_refund", self.vendor)
        self._link_move_lines(invoice, self.property)
        self._link_move_lines(refund, self.property)
        self._link_move_lines(bill, self.property)
        self._link_move_lines(credit, self.property)
        self.assertEqual(self.property.invoice_count, 2)
        self.assertEqual(self.property.bill_count, 2)

    def test_action_view_invoices_single(self):
        move = self._create_move("out_invoice", self.customer)
        self._link_move_lines(move, self.property)
        action = self.property.action_view_invoices()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "account.move")
        self.assertEqual(action["res_id"], move.id)

    def test_action_view_invoices_multiple(self):
        move1 = self._create_move("out_invoice", self.customer)
        move2 = self._create_move("out_invoice", self.customer)
        self._link_move_lines(move1, self.property)
        self._link_move_lines(move2, self.property)
        action = self.property.action_view_invoices()
        self.assertEqual(
            action["domain"], [("id", "in", self.property.invoice_ids.ids)]
        )

    def test_action_view_bills_single(self):
        move = self._create_move("in_invoice", self.vendor)
        self._link_move_lines(move, self.property)
        action = self.property.action_view_bills()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "account.move")
        self.assertEqual(action["res_id"], move.id)

    def test_action_view_bills_multiple(self):
        move1 = self._create_move("in_invoice", self.vendor)
        move2 = self._create_move("in_invoice", self.vendor)
        self._link_move_lines(move1, self.property)
        self._link_move_lines(move2, self.property)
        action = self.property.action_view_bills()
        self.assertEqual(action["domain"], [("id", "in", self.property.bill_ids.ids)])

    def test_move_property_ids_compute(self):
        move = self._create_move("out_invoice", self.customer)
        self._link_move_lines(move, self.property, self.property2)
        self.assertEqual(move.property_count, 2)
        self.assertEqual(
            set(move.property_ids.ids), {self.property.id, self.property2.id}
        )

    def test_move_action_view_pms_property_single(self):
        move = self._create_move("out_invoice", self.customer)
        self._link_move_lines(move, self.property)
        action = move.action_view_pms_property()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "pms.property")
        self.assertEqual(action["res_id"], self.property.id)

    def test_move_action_view_pms_property_multiple(self):
        move = self._create_move("out_invoice", self.customer)
        self._link_move_lines(move, self.property, self.property2)
        action = move.action_view_pms_property()
        self.assertEqual(action["domain"], [("id", "in", move.property_ids.ids)])

    def test_move_action_view_pms_property_empty(self):
        move = self._create_move("out_invoice", self.customer)
        action = move.action_view_pms_property()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "pms.property")
        self.assertEqual(move.property_count, 0)

    def test_invoice_line_property_ids(self):
        move = self._create_move("out_invoice", self.customer)
        self._link_move_lines(move, self.property)
        line = move.invoice_line_ids[0]
        self.assertIn(self.property, line.property_ids)

    def test_service_vendor_required(self):
        service = self.env["pms.service"].create(
            {
                "name": self.product.id,
                "property_id": self.property.id,
                "vendor_id": self.vendor.id,
            }
        )
        self.assertEqual(service.vendor_id, self.vendor)
