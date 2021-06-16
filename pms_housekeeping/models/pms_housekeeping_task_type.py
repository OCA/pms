# Copyright 2020 Jose Luis Algara (Alda Hotels <https://www.aldahotels.es>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PmsHouseKeepingTaskType(models.Model):
    _name = "pms.housekeeping.task.type"
    _description = "HouseKeeping Task Types"

    active = fields.Boolean(string="Active", default=True)
    name = fields.Char(string="Task Name", translate=True, required=True)
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        required=False,
        comodel_name="pms.property",
        relation="pms_housekeepink_task_pms_property_rel",
        column1="pms_housekeepink_task_id",
        column2="pms_property_id",
        ondelete="restrict",
        check_pms_properties=True,
    )

    clean_type = fields.Selection(
        string="Clean type",
        selection=[
            ("occupied", "Occupied"),
            ("exit", "Exit"),
            ("picked_up", "Picked up"),
            ("staff", "Staff"),
            ("clean", "Clean"),
            ("inspected", "Inspected"),
            ("dont_disturb", "Don't disturb"),
        ],
    )
    default_employee_id = fields.Many2one(
        string="Default House Keeper",
        help="Employee assigned by default",
        comodel_name="hr.employee",
    )
