# Copyright 2024 OsoTranquilo - José Luis Algara
# Copyright 2024 Irlui Ramírez
# From Consultores Hoteleros Integrales (ALDA Hotels) - 2024
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PmsHrProperty(models.Model):
    _inherit = "pms.property"

    employee_ids = fields.Many2many(
        comodel_name="hr.employee",
        string="Assigned Employees",
        compute="_compute_employee_ids",
    )

    # @api.depends('employee_ids')
    # def _compute_employee_ids(self):
    #     specific_job_names = ['Regional Manager','Revenue Manager', 'TAZ', 'TMZ']
    #     for record in self:
    #         specific_jobs = self.env['hr.job'].search([('name', 'in', specific_job_names)])
    #         specific_job_ids = specific_jobs.ids
    #         employees = self.env['hr.employee'].search([
    #             ('property_ids', 'in', record.id),
    #             ('job_id', 'in', specific_job_ids)
    #         ])
    #         record.employee_ids = employees

    @api.depends("employee_ids")
    def _compute_employee_ids(self):
        for record in self:
            employees = self.env["hr.employee"].search(
                [("property_ids", "in", record.id)]
            )
            record.employee_ids = employees
