from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    channel_available = fields.Boolean(
        string="Sale Channel Available",
        help="If checked, the product will be available for Channel",
        default=False,
    )
