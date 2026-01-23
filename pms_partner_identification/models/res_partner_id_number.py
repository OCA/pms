from odoo import fields, models


class ResPartnerIdNumber(models.Model):
    _inherit = "res.partner.id_number"

    category_id = fields.Many2one(
        domain="['|', ('country_ids', '=', False),"
        " ('country_ids', 'in', country_id)]",
    )
    country_id = fields.Many2one(
        string="Country",
        comodel_name="res.country",
        help="Country of the document",
    )

    _sql_constraints = [
        (
            "unique_category_by_partner",
            "unique(partner_id, category_id)",
            "Partner already has this document type!",
        ),
    ]
