from odoo import SUPERUSER_ID
from odoo.api import Environment


def pre_init_hook(cr):
    env = Environment(cr, SUPERUSER_ID, {})
    ResConfig = env["res.config.settings"]
    default_values = ResConfig.default_get(list(ResConfig.fields_get()))
    default_values.update(
        {"group_product_pricelist": True, "group_sale_pricelist": True}
    )
    ResConfig.sudo().create(default_values).execute()
    env["ir.config_parameter"].sudo().set_param(
        "product.product_pricelist_setting", "advanced"
    )
