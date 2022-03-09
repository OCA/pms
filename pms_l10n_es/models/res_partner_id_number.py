from odoo import fields, models


class ResPartnerIdNumber(models.Model):
    _inherit = "res.partner.id_number"
    _description = "Partner ID Number"

    support_number = fields.Char(string="Support number", help="DNI support number")
