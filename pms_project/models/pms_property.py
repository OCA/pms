# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    task_ids = fields.Many2many(
        "project.task", "task_property_rel", "property_id", "task_id", string="Tasks"
    )
