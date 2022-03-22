# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    reservation_count = fields.Integer(
        "Reservations Count", compute="_compute_reservation_count"
    )

    @api.depends("line_ids")
    def _compute_reservation_count(self):
        for invoice in self:
            reservation = invoice.line_ids.mapped("pms_reservation_id")
            invoice.reservation_count = len(reservation)

    def action_view_reservation_list(self):
        for invoice in self:
            action = self.env["ir.actions.actions"]._for_xml_id(
                "pms_sale.action_pms_reservation"
            )
            reservation = self.line_ids.mapped("pms_reservation_id")
            action["domain"] = [
                ("id", "in", reservation.ids),
                ("partner_id", "=", invoice.partner_id.id),
            ]
            return action
