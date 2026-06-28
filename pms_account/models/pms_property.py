# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# Copyright (c) 2021 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    analytic_id = fields.Many2one(
        string="Analytic Account",
        comodel_name="account.analytic.account",
    )

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        for rec in recs:
            if not rec.analytic_id:
                rec._create_analytic_account()
        return recs

    def write(self, vals):
        res = super().write(vals)
        if "name" in vals or "ref" in vals:
            for rec in self:
                if rec.analytic_id:
                    rec.analytic_id.name = rec.name
                    rec.analytic_id.code = rec.ref
                else:
                    rec._create_analytic_account()
        return res

    def _create_analytic_account(self):
        plan = self.env.ref(
            "pms_account.analytic_plan_properties", raise_if_not_found=False
        )
        if not plan:
            return
        analytic = self.env["account.analytic.account"].create(
            {
                "name": self.name,
                "plan_id": plan.id,
                "code": self.ref,
                "property_id": self.id,
            }
        )
        self.analytic_id = analytic.id

    invoice_line_ids = fields.Many2many(
        "account.move.line",
        "pms_property_account_move_line_rel",
        "property_id",
        "account_move_line_id",
        string="Invoice Lines",
        copy=False,
    )
    invoice_ids = fields.Many2many(
        "account.move",
        string="Invoices",
        compute="_compute_invoice_count",
        readonly=True,
        copy=False,
    )
    bill_ids = fields.Many2many(
        "account.move",
        string="Bills",
        compute="_compute_invoice_count",
        readonly=True,
        copy=False,
    )
    invoice_count = fields.Integer(
        compute="_compute_invoice_count",
        readonly=True,
        copy=False,
    )
    bill_count = fields.Integer(
        compute="_compute_invoice_count",
        readonly=True,
        copy=False,
    )

    @api.depends("invoice_line_ids")
    def _compute_invoice_count(self):
        for rec in self:
            invoices = rec.invoice_line_ids.mapped("move_id").filtered(
                lambda r: r.move_type in ("out_invoice", "out_refund")
            )
            bills = rec.invoice_line_ids.mapped("move_id").filtered(
                lambda r: r.move_type in ("in_invoice", "in_refund")
            )
            rec.invoice_ids = invoices
            rec.invoice_count = len(invoices)
            rec.bill_ids = bills
            rec.bill_count = len(bills)

    def action_view_invoices(self):
        action = self.env.ref("account.action_move_out_invoice_type").read()[0]
        invoices = self.mapped("invoice_ids")
        if len(invoices) > 1:
            action["domain"] = [("id", "in", invoices.ids)]
        elif invoices:
            action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
            action["res_id"] = invoices.ids[0]
        return action

    def action_view_bills(self):
        action = self.env.ref("account.action_move_in_invoice_type").read()[0]
        bills = self.mapped("bill_ids")
        if len(bills) > 1:
            action["domain"] = [("id", "in", bills.ids)]
        elif bills:
            action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
            action["res_id"] = bills.ids[0]
        return action
