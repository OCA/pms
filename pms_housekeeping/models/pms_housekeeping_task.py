# Copyright 2020 Jose Luis Algara (Alda Hotels <https://www.aldahotels.es>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PmsHouseKeepingTask(models.Model):
    _name = "pms.housekeeping.task"
    _description = "HouseKeeping Task"

    task_date = fields.Date(
        string="Clean date",
        help="Date the task was done or;" " is scheduled to be done",
        default=lambda self: fields.Datetime.now(),
        required=True,
    )
    task_start = fields.Datetime(string="Task start at")
    task_end = fields.Datetime(string="Task end at")
    room_id = fields.Many2one(
        comodel_name="pms.room",
        string="Room",
    )
    employee_id = fields.Many2one(
        string="Employee",
        comodel_name="hr.employee",
    )
    task_type_id = fields.Many2one(
        string="Task",
        comodel_name="pms.housekeeping.task.type",
        required=True,
    )
    notes = fields.Text(string="Internal Notes")
    lostfound = fields.Text(string="Lost and Found")
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
    color = fields.Integer(string="Color Index")

    # Default Methods ang Gets
    def name_get(self):
        result = []
        for task in self:
            name = task.task_type_id.name
            result.append((task.id, name))
        return result
