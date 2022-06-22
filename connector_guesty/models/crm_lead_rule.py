# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CrmLeadRule(models.Model):
    _name = "crm.lead.rule"
    _description = "Lead rule"

    backend_id = fields.Many2one("backend.guesty")
    expression_string = fields.Text()
    is_html = fields.Boolean()
    lead_field = fields.Char()
