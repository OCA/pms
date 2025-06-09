from odoo import fields, models


class ResPartnerIdCategory(models.Model):
    _inherit = "res.partner.id_category"

    country_ids = fields.Many2many(
        comodel_name="res.country",
        string="Countries",
    )

    priority = fields.Integer(
        default=100,
    )
