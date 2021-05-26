# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    pms_property_ids = fields.One2many(
        string="Properties",
        help="Properties with access to the element",
        comodel_name="pms.property",
        inverse_name="company_id",
    )
