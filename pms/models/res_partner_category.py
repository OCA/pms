from odoo import fields, models


class ResPartnerCategory(models.Model):
    _inherit = "res.partner.category"

    is_used_in_checkin = fields.Boolean(string="Used in checkin")
