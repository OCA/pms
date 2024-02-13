from odoo import fields, models


class PmsHouseKeepingTaskType(models.Model):
    _name = "pms.housekeeping.task.type"

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
    is_automated = fields.Boolean(string="Is Automated")
    is_overnight = fields.Boolean(string="Overnight")
    is_empty = fields.Boolean(string="Empty")
    is_checkin = fields.Boolean(string="Checkin")
    is_checkout = fields.Boolean(string="Checkout")
    priority = fields.Integer(string="Priority", default=0)
    days_after_clean_overnight = fields.Integer(
        string="Days After Clean Overnight",
    )
    days_after_clean_empty = fields.Integer(
        string="Days After Clean Empty",
    )
    housekeeper_ids = fields.Many2many(
        comodel_name="hr.employee",
        relation="pms_housekeeping_task_type_hr_employee_rel",
        column1="task_type_id",
        column2="employee_id",
        string="Housekeepers",
        domain="[('job_id.name', '=', 'Housekeeper')]",
    )
    parent_id = fields.Many2one(
        string="Parent Task Type",
        help="Indicates that this task type is a child of another task type",
        comodel_name="pms.housekeeping.task.type",
        domain="[('id', '!=', id)]",
    )
    is_inspection = fields.Boolean(string="Inspection")
