from odoo import fields, models, api


class Country(models.Model):
    _inherit = 'res.country'
    _description = 'Country'
    _order = 'priority, name'

    priority = fields.Integer(string='Priority', default=1000)
