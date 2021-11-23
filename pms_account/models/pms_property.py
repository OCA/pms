# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    analytic_id = fields.Many2one(
        string="Analytic Account",
        comodel_name="account.analytic.account",
    )
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
        string="Invoice Count",
        compute="_compute_invoice_count",
        readonly=True,
        copy=False,
    )
    bill_count = fields.Integer(
        string="Bill Count",
        compute="_compute_invoice_count",
        readonly=True,
        copy=False,
    )

    @api.depends("invoice_line_ids")
    def _compute_invoice_count(self):
        for property in self:
            invoices = property.invoice_line_ids.mapped("move_id").filtered(
                lambda r: r.move_type in ("out_invoice", "out_refund")
            )
            bills = property.invoice_line_ids.mapped("move_id").filtered(
                lambda r: r.move_type in ("in_invoice", "in_refund")
            )
            property.invoice_ids = invoices
            property.invoice_count = len(invoices)
            property.bill_ids = bills
            property.bill_count = len(bills)

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
