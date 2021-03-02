# Copyright 2020 Jose Luis Algara (Alda Hotels <https://www.aldahotels.es>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HouseKeeping(models.Model):
    _name = "pms.housekeeping"
    _description = "HouseKeeping"
    # HouseKeeping 'log'

    # Fields declaration

    task_date = fields.Date(
        string="Clean date", default=lambda self: fields.Datetime.now(), required=True
    )
    task_start = fields.Datetime(string="Task start at")
    task_end = fields.Datetime(string="Task end at")
    room_id = fields.Many2one("pms.room", string="Room")
    employee_id = fields.Many2one("hr.employee", string="Employee")
    task_id = fields.Many2one("pms.housekeeping.task", string="Task", required=True)
    notes = fields.Text("Internal Notes")
    lostfound = fields.Text("Lost and Found")
    state = fields.Selection(
        string="Task State",
        selection=[
            ("draft", "Draft"),
            ("to_do", "To Do"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
        ],
        default="draft",
    )
    color = fields.Integer("Color Index")

    # Default Methods ang Gets
    def name_get(self):
        result = []
        for task in self:
            name = task.task_id.name
            result.append((task.id, name))
        return result
