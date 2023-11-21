# Copyright 2023 Comunitea S.L. (http://www.comunitea.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveBudgetLine(models.Model):
    _inherit = "account.move.budget.line"

    pms_property_id = fields.Many2one(
        "pms.property", string="Hotel", required=False, index=True
    )
