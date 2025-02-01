from odoo import fields, models


class ResPartnerIdCategory(models.Model):
    _inherit = "res.partner.id_category"

    klippa_code = fields.Char()
    klippa_subtype_code = fields.Char()
