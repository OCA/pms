from odoo import fields, models


class PmsHouseKeepingTask(models.Model):
    _name = "pms.housekeeping.task"

    name = fields.Char(string="Name", required=True)
    room_id = fields.Many2one(
        comodel_name="pms.room",
        string="Room",
        required=True,
        ondelete="restrict",
    )
    task_type_id = fields.Many2one(
        comodel_name="pms.housekeeping.task.type",
        string="Task Type",
        required=True,
        ondelete="restrict",
    )
    task_datetime = fields.Datetime(string="Date")
    state = fields.Selection(
        selection=[
            ("holding", "On Holding"),
            ("to_do", "To Do"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
            ("cancel", "Cancel"),
        ],
        string="State",
        required=True,
        default="to_do",
    )
    priority = fields.Integer(string="Priority", default=0)
    cleaning_comments = fields.Text(string="Cleaning Comments")
    employee_ids = fields.Many2many(
        comodel_name="hr.employee",
        relation="pms_housekeeping_task_hr_employee_rel",
        column1="task_id",
        column2="employee_id",
        string="Employees",
        domain="[('job_id.name', '=', 'Housekeeper')]",
    )
    parent_id = fields.Many2one(
        string="Parent Task",
        help="Indicates that this task is a child of another task",
        comodel_name="pms.housekeeping.task",
        ondelete="restrict",
    )
