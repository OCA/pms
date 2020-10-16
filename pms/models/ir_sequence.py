# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    pms_property_id = fields.Many2one("pms.property", string="Property")
