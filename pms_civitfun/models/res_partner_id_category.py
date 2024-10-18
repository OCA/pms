from odoo import fields, models


class ResPartnerIdCategory(models.Model):
    _inherit = "res.partner.id_category"

    civitfun_category = fields.Char(
        string="Civitfun Category",
        help="Civitfun Category",
    )
