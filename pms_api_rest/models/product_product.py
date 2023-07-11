from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    channel_available = fields.Boolean(
        string="Sale Channel Available",
        help="If checked, the product will be available for Channel",
        default=False,
    )
