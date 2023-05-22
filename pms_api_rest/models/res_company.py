from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    url_app = fields.Char(string="Url App", help="Url to identify the app")
