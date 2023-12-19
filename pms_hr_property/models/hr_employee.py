# Copyright 2023 OsoTranquilo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields, models


class HrEmployeeBase(models.AbstractModel):

    _inherit = "hr.employee.base"

    property_ids = fields.Many2many("pms.property", string="Workplaces asigned")
