from odoo import fields, models


class Country(models.Model):
    _inherit = "res.country"
    _description = "Country"
    _order = "priority, name"

    priority = fields.Integer(default=1000)
