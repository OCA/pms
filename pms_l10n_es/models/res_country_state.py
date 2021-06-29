from odoo import fields, models


class ResCountryState(models.Model):
    _inherit = "res.country.state"
    ine_code = fields.Char(string="INE State Code")
