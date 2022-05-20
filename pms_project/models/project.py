# Copyright (C) 2022 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class Project(models.Model):
    _inherit = "project.project"

    property_id = fields.Many2one("pms.property", string="Property")
