# Copyright 2024 OsoTranquilo - José Luis Algara
# Copyright 2024 Irlui Ramírez
# From Consultores Hoteleros Integrales (ALDA Hotels) - 2024
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsHrProperty(models.Model):
    _inherit = "pms.property"

    employee_ids = fields.Many2many(
        comodel_name="hr.employee",
        string="Assigned Employees",
        relation="hr_employee_pms_property_rel",
        column1="pms_property_id",
        column2="hr_employee_id",
    )
