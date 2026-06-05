# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    stock_location_id = fields.Many2one("stock.location", string="Inventory Location")
