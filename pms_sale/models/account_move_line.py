# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    pms_reservation_id = fields.Many2one(
        "pms.reservation", string="Reservation", readonly=True, copy=False
    )
