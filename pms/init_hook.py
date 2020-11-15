from odoo import SUPERUSER_ID
from odoo.api import Environment


def post_init_hook(cr, _):
    with Environment.manage():
        env = Environment(cr, SUPERUSER_ID, {})
        env["ir.config_parameter"].sudo().set_param(
            "product.product_pricelist_setting", "advanced"
        )
