# Copyright 2020 Jose Luis Algara (Alda Hotels <https://www.aldahotels.es>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    pre_assigned_room_ids = fields.Many2many(
        comodel_name="pms.room",
        string="Pre Assigned Rooms",
        help="Rooms pre assigned to this employee",
    )

    job_name = fields.Char(string="Job Name", compute="_compute_job_name")

    @api.depends("job_id")
    def _compute_job_name(self):
        for record in self:
            record.job_name = record.job_id.name
