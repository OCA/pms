# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    pms_property_ids = fields.Many2many(
        "pms.property",
        "task_property_rel",
        "task_id",
        "property_id",
        string="Properties",
    )
