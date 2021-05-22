from odoo import fields, models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    pms_property_id = fields.Many2one(
        string="Property",
        help="Properties with access to the element",
        copy=False,
        comodel_name="pms.property",
    )
    company_id = fields.Many2one(
        string="Company",
        help="The company for Account Bank Statement",
    )
