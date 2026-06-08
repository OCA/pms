# Copyright (c) 2021 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import timedelta

from odoo import fields, models


class PMSTeam(models.Model):
    _inherit = "pms.team"

    no_today_reservation = fields.Integer(
        string="Today Reservations", compute="_compute_no_reservations"
    )
    no_tomorrow_reservation = fields.Integer(
        string="Tomorrow Reservations", compute="_compute_no_reservations"
    )
    no_week_reservation = fields.Integer(
        string="This Week Reservations", compute="_compute_no_reservations"
    )
    total_reservation = fields.Integer(
        string="Total Reservations", compute="_compute_no_reservations"
    )

    def _compute_no_reservations(self):
        start = fields.Date.today() - timedelta(days=fields.Date.today().weekday())
        end = start + timedelta(days=6)
        reservation_obj = self.env["pms.reservation"]
        for rec in self:
            today_reservation_count = reservation_obj.search_count(
                [
                    ("team_id", "=", rec.id),
                    ("start", ">=", fields.Date.today()),
                    ("start", "<=", fields.Date.today()),
                    (
                        "stage_id",
                        "!=",
                        self.env.ref("pms_sale.pms_stage_checked_out").id,
                    ),
                    ("stage_id", "!=", self.env.ref("pms_sale.pms_stage_cancelled").id),
                ]
            )
            tomorrow_reservation_count = reservation_obj.search_count(
                [
                    ("team_id", "=", rec.id),
                    ("start", ">=", fields.Date.today()),
                    ("stop", "<=", fields.Date.today() + timedelta(1)),
                    (
                        "stage_id",
                        "!=",
                        self.env.ref("pms_sale.pms_stage_checked_out").id,
                    ),
                    ("stage_id", "!=", self.env.ref("pms_sale.pms_stage_cancelled").id),
                ]
            )
            this_week_reservation_count = reservation_obj.search_count(
                [
                    ("team_id", "=", rec.id),
                    ("start", ">=", start),
                    ("stop", "<=", end),
                    (
                        "stage_id",
                        "!=",
                        self.env.ref("pms_sale.pms_stage_checked_out").id,
                    ),
                    ("stage_id", "!=", self.env.ref("pms_sale.pms_stage_cancelled").id),
                ]
            )
            total_reservation_count = reservation_obj.search_count(
                [
                    ("team_id", "=", rec.id),
                    (
                        "stage_id",
                        "!=",
                        self.env.ref("pms_sale.pms_stage_checked_out").id,
                    ),
                    ("stage_id", "!=", self.env.ref("pms_sale.pms_stage_cancelled").id),
                ]
            )

            rec.no_today_reservation = today_reservation_count
            rec.no_tomorrow_reservation = tomorrow_reservation_count
            rec.no_week_reservation = this_week_reservation_count
            rec.total_reservation = total_reservation_count
