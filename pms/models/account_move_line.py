# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Fields declaration
    reservation_ids = fields.Many2many(
        "pms.reservation",
        "reservation_move_rel",
        "move_line_id",
        "reservation_id",
        string="Reservations",
        readonly=True,
        copy=False,
    )
    service_ids = fields.Many2many(
        "pms.service",
        "service_line_move_rel",
        "move_line_id",
        "service_id",
        string="Services",
        readonly=True,
        copy=False,
    )
    reservation_line_ids = fields.Many2many(
        "pms.reservation.line",
        "reservation_line_move_rel",
        "move_line_id",
        "reservation_line_id",
        string="Reservation Lines",
        readonly=True,
        copy=False,
    )
