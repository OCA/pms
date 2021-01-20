from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.depends_context(
        "pricelist",
        "partner",
        "quantity",
        "uom",
        "date",
        "date_overnight",
        "no_variant_attributes_price_extra",
    )
    def _compute_product_price(self):
        super(ProductProduct, self)._compute_product_price()
