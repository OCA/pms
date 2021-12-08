# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    pms_uom = fields.Selection(
        [("ft", "Square Foot"), ("m", "Square Meter")],
        string="Unit of Measure",
        default="m",
    )
