from odoo import fields, models


class PmsHouseKeepingTaskType(models.Model):
    _name = "pms.housekeeping.task.type"

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
    is_automated = fields.Boolean(string="Is Automated")
    clean_event = fields.Selection(
        selection=[
            ("overnight", "Overnight"),
            ("checkin", "Checkin"),
            ("checkout", "Checkout"),
            ("empty", "Empty"),
            ("priority", "Priority"),
        ],
        string="Clean When",
        required=True,
        default="overnight",
    )
    days_after_clean_event = fields.Integer(string="Days After Clean Event")
    housekeepers = fields.Many2many(
        comodel_name="hr.employee",
        relation="pms_housekeeping_task_type_hr_employee_rel",
        column1="task_type_id",
        column2="employee_id",
        string="Housekeepers",
        domain="[('job_id.name', '=', 'Housekeeper')]",
    )
    parent_id = fields.Many2many(
        string="Parent Task Type",
        help="Indicates that this task type is a child of another task type",
        comodel_name="pms.housekeeping.task.type",
        relation="pms_housekeeping_task_type_rel",
        column1="parent_task_type_id",
        column2="child_task_type_id",
        ondelete="restrict",
        domain="[('id', '!=', id)]",
    )
