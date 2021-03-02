# Copyright 2020 Jose Luis Algara (Alda Hotels <https://www.aldahotels.es>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HouseKeepingTask(models.Model):
    _name = "pms.housekeeping.task"
    _description = "HouseKeeping Tasks"
    # HouseKeeping 'Task types'

    # Fields declaration
    active = fields.Boolean("Active", default=True)
    name = fields.Char("Task Name", translate=True, required=True)
    pms_property_ids = fields.Many2many(
        "pms.property", string="Properties", required=False, ondelete="restrict"
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
    def_employee_id = fields.Many2one(
        "hr.employee", string="Employee assigned by default"
    )
