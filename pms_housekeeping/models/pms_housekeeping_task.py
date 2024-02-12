from odoo import fields, models, api
from odoo.exceptions import ValidationError


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
    task_date = fields.Date(string="Date", required=True,)
    state = fields.Selection(
        selection=[
            ("pending", "Pending"),
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
        domain="[('id', '!=', id)]",
    )
    parent_state = fields.Char(
        string="Parent State",
        compute="_compute_parent_state",
    )
    cancellation_type_id = fields.Many2one(
        comodel_name="pms.housekeeping.cancellation.type",
        string="Cancellation Type",
        ondelete="restrict",
    )
    is_today = fields.Boolean(
        string="Is Today",
        compute="_compute_is_today",
        store=True,
        readonly=False,
    )
    is_future = fields.Boolean(
        string="Is Future",
        compute="_compute_is_future",
    )

    @api.constrains("task_date")
    def _check_task_date(self):
        for rec in self:
            if rec.task_date < fields.Date.today():
                raise ValidationError("Task Date must be greater than or equal to today")

    def action_cancel(self):
        for rec in self:
            rec.state = "cancel"

    def action_to_do(self):
        for rec in self:
            rec.state = "to_do"

    def action_done(self):
        for rec in self:
            rec.state = "done"

    def action_in_progress(self):
        for rec in self:
            rec.state = "in_progress"

    def action_pending(self):
        for rec in self:
            rec.state = "pending"

    @api.depends("parent_id.state")
    def _compute_parent_state(self):
        for rec in self:
            rec.parent_state = rec.parent_id.state if rec.parent_id else False

    @api.depends("task_date")
    def _compute_is_today(self):
        for rec in self:
            if rec.task_date:
                rec.is_today = rec.task_date == fields.Date.today()
            else:
                rec.is_today = False
    @api.depends("task_date")
    def _compute_is_future(self):
        for rec in self:
            if rec.task_date:
                rec.is_future = rec.task_date > fields.Date.today()
            else:
                rec.is_future = False
