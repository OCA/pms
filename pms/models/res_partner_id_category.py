from odoo import fields, models


class ResPartnerIdCategory(models.Model):
    _inherit = "res.partner.id_category"

    is_vat_equivalent = fields.Boolean(
        string="Is VAT Equivalent",
        help="If true, this document type is check by vat number",
        default=False,
    )
