from odoo import _, api, fields, models
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
    task_date = fields.Date(
        string="Date",
        required=True,
    )
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
        default="pending",
    )
    priority = fields.Integer(
        string="Priority",
        default=0,
        computed="_compute_priority",
        store=True,
        readonly=False,
    )
    cleaning_comments = fields.Text(string="Cleaning Comments")
    employee_ids = fields.Many2many(
        comodel_name="hr.employee",
        relation="pms_housekeeping_task_hr_employee_rel",
        column1="task_id",
        column2="employee_id",
        string="Employees",
        domain="[('job_id.name', '=', 'Housekeeper')]",
        compute="_compute_employee_ids",
        store=True,
        readonly=False,
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
    child_ids = fields.One2many(
        string="Child Tasks",
        help="Indicates that this task has child tasks",
        comodel_name="pms.housekeeping.task",
        inverse_name="parent_id",
    )
    cancellation_type_id = fields.Many2one(
        comodel_name="pms.housekeeping.cancellation.type",
        string="Cancellation Type",
        ondelete="restrict",
    )
    pending_allowed = fields.Boolean(
        string="Is pending allowed",
        compute="_compute_pending_allowed",
    )
    to_do_allowed = fields.Boolean(
        string="Is To Do Allowed",
        compute="_compute_to_do_allowed",
    )
    cancel_allowed = fields.Boolean(
        string="Is Cancel Allowed",
        compute="_compute_cancel_allowed",
    )
    in_progress_allowed = fields.Boolean(
        string="Is In Progress Allowed",
        compute="_compute_in_progress_allowed",
    )
    done_allowed = fields.Boolean(
        string="Is Done Allowed",
        compute="_compute_done_allowed",
    )

    @api.constrains("task_date")
    def _check_task_date(self):
        for rec in self:
            if rec.task_date < fields.Date.today():
                raise ValidationError(
                    _("Task Date must be greater than or equal to today")
                )

    def action_cancel(self):
        for rec in self:
            rec.state = "cancel"

    def action_to_do(self):
        for rec in self:
            rec.state = "to_do"
            rec.cancellation_type_id = False

    def action_done(self):
        for rec in self:
            rec.state = "done"
            rec.cancellation_type_id = False

    def action_in_progress(self):
        for rec in self:
            rec.state = "in_progress"
            rec.cancellation_type_id = False

    def action_pending(self):
        for rec in self:
            rec.state = "pending"
            rec.cancellation_type_id = False

    @api.onchange("state")
    def _onchange_state(self):
        for rec in self:
            if rec.state == "cancel":
                rec.child_ids.state = "cancel"
            elif rec.state != "done":
                rec.child_ids.state = "pending"

    @api.depends("parent_id.state")
    def _compute_parent_state(self):
        for rec in self:
            rec.parent_state = rec.parent_id.state if rec.parent_id else False

    @api.depends("task_date", "state")
    def _compute_pending_allowed(self):
        for rec in self:
            if (
                rec.task_date
                and rec.state == "cancel"
                and (
                    rec.task_date > fields.Date.today()
                    or (
                        (rec.parent_state and rec.parent_state != "done")
                        or not rec.parent_state
                    )
                )
            ):
                rec.pending_allowed = True
            else:
                rec.pending_allowed = False

    @api.depends("task_date", "state")
    def _compute_to_do_allowed(self):
        for rec in self:
            if (
                rec.task_date
                and rec.task_date == fields.Date.today()
                and rec.state in ("cancel", "pending", "done", "in_progress")
                and (
                    (rec.parent_state and rec.parent_state == "done")
                    or not rec.parent_state
                )
            ):
                rec.to_do_allowed = True
            else:
                rec.to_do_allowed = False

    @api.depends("state")
    def _compute_cancel_allowed(self):
        for rec in self:
            if rec.state in ("to_do", "pending"):
                rec.cancel_allowed = True
            else:
                rec.cancel_allowed = False

    @api.depends("state")
    def _compute_in_progress_allowed(self):
        for rec in self:
            if rec.state == "to_do":
                rec.in_progress_allowed = True
            else:
                rec.in_progress_allowed = False

    @api.depends("state")
    def _compute_done_allowed(self):
        for rec in self:
            if rec.state == "in_progress":
                rec.done_allowed = True
            else:
                rec.done_allowed = False

    @api.depends("room_id", "task_type_id")
    def _compute_employee_ids(self):
        for rec in self:
            employee_ids = False
            if rec.room_id or rec.task_type_id:
                employee_ids = self.env["hr.employee"].search(
                    [("pre_assigned_room_ids", "in", [rec.room_id.id])]
                )
                if not employee_ids:
                    employee_ids = (
                        self.env["pms.housekeeping.task.type"]
                        .search([("id", "=", rec.task_type_id.id)])
                        .housekeeper_ids
                    )
            rec.employee_ids = employee_ids

    @api.depends("task_type_id")
    def _compute_priority(self):
        for rec in self:
            if rec.task_type_id:
                rec.priority = rec.task_type_id.priority
            else:
                rec.priority = False

    @api.model
    def create(self, vals):
        task_type_id = vals.get("task_type_id")
        pms_housekeeping_task_type = self.env["pms.housekeeping.task.type"].browse(
            task_type_id
        )
        room_id = vals.get("room_id")
        pms_room = self.env["pms.room"].browse(room_id)
        pms_room.housekeeping_state = (
            "to_inspect" if pms_housekeeping_task_type.is_inspection else "dirty"
        )

        return super(PmsHouseKeepingTask, self).create(vals)
