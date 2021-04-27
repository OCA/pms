from odoo import fields, models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    property_id = fields.Many2one("pms.property", string="Property", copy=False)
    company_id = fields.Many2one(
        check_pms_properties=True,
    )
