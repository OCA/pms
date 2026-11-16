# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# Copyright (c) 2021 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

INVOICE_MOVE_TYPES = ("out_invoice", "out_refund")
BILL_MOVE_TYPES = ("in_invoice", "in_refund")


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
        compute="_compute_invoice_ids",
        readonly=True,
        copy=False,
    )
    bill_ids = fields.Many2many(
        "account.move",
        string="Bills",
        compute="_compute_invoice_ids",
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
    def _compute_invoice_ids(self):
        for rec in self:
            moves = rec.invoice_line_ids.move_id
            rec.invoice_ids = moves.filtered(
                lambda move: move.move_type in INVOICE_MOVE_TYPES
            )
            rec.bill_ids = moves.filtered(
                lambda move: move.move_type in BILL_MOVE_TYPES
            )

    @api.depends("invoice_line_ids")
    def _compute_invoice_count(self):
        for rec in self:
            move_counts = dict(
                self.env["account.move"]._read_group(
                    [
                        ("move_type", "in", INVOICE_MOVE_TYPES + BILL_MOVE_TYPES),
                        ("line_ids", "any", [("property_ids", "=", rec.id)]),
                    ],
                    ["move_type"],
                    ["__count"],
                )
            )
            rec.invoice_count = sum(
                move_counts.get(move_type, 0) for move_type in INVOICE_MOVE_TYPES
            )
            rec.bill_count = sum(
                move_counts.get(move_type, 0) for move_type in BILL_MOVE_TYPES
            )

    def _get_move_domain(self, move_types):
        return [
            ("move_type", "in", move_types),
            ("line_ids", "any", [("property_ids", "in", self.ids)]),
        ]

    def action_view_invoices(self):
        action = self.env.ref("account.action_move_out_invoice_type").read()[0]
        action["domain"] = self._get_move_domain(INVOICE_MOVE_TYPES)
        if self.invoice_count == 1:
            move_id = self.env["account.move"].search(action["domain"], limit=1)
            action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
            action["res_id"] = move_id.id
        return action

    def action_view_bills(self):
        action = self.env.ref("account.action_move_in_invoice_type").read()[0]
        action["domain"] = self._get_move_domain(BILL_MOVE_TYPES)
        if self.bill_count == 1:
            move_id = self.env["account.move"].search(action["domain"], limit=1)
            action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
            action["res_id"] = move_id.id
        return action
