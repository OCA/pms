from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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
    )
    parent_id = fields.Many2one(
        string="Parent Task Type",
        help="Indicates that this task type is a child of another task type",
        comodel_name="pms.housekeeping.task.type",
        domain="[('id', '!=', id)]",
    )
    child_ids = fields.One2many(
        string="Child Task Types",
        comodel_name="pms.housekeeping.task.type",
        inverse_name="parent_id",
    )
    is_inspection = fields.Boolean(string="Inspection")

    pms_property_ids = fields.Many2many(
        comodel_name="pms.property",
        relation="pms_housekeeping_task_type_pms_property_rel",
        column1="task_type_id",
        column2="property_id",
        string="Properties",
    )

    allowed_housekeeper_ids = fields.Many2many(
        comodel_name="hr.employee",
        relation="pms_housekeeping_task_type_allowed_hr_employee_rel",
        column1="task_type_id",
        column2="employee_id",
        string="Allowed Employees",
        compute="_compute_allowed_housekeeper_ids",
    )

    @api.constrains("is_overnight", "days_after_clean_overnight")
    def _check_days_after_clean_overnight(self):
        for record in self:
            if record.is_overnight and record.days_after_clean_overnight <= 0:
                raise ValidationError(
                    _("Days After Clean Overnight should be greater than 0")
                )

    @api.constrains("is_empty", "days_after_clean_empty")
    def _check_days_after_clean_empty(self):
        for record in self:
            if record.is_empty and record.days_after_clean_empty <= 0:
                raise ValidationError(
                    _("Days After Clean Empty should be greater than 0")
                )

    @api.constrains("parent_id")
    def _check_parent_id(self):
        for rec in self:
            if rec.parent_id.parent_id:
                raise ValidationError(
                    _("Parent task type cannot have a parent task type")
                )

    @api.depends("pms_property_ids")
    def _compute_allowed_housekeeper_ids(self):
        for record in self:
            domain = []
            if record.pms_property_ids:
                domain = [
                    "|",
                    ("property_ids", "in", record.pms_property_ids.ids),
                    ("property_ids", "in", False),
                ]
            domain.append(("job_id.name", "=", "Housekeeper"))
            record.allowed_housekeeper_ids = self.env["hr.employee"].search(domain).ids
