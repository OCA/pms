# Copyright 2023 OsoTranquilo
# Copyright 2024 Irlui Ramírez
# From Consultores Hoteleros Integrales (ALDA Hotels) - 2024
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class HrEmployeeBase(models.AbstractModel):

    _inherit = "hr.employee.base"

    property_ids = fields.Many2many(
        comodel_name="pms.property",
        string="Workplaces asigned",
        relation="hr_employee_pms_property_rel",
        column1="hr_employee_id",
        column2="pms_property_id",
    )
