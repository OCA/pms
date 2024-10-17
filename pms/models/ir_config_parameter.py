from odoo import _, api, models
from odoo.exceptions import ValidationError


class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    def unlink(self):
        for record in self:
            if (
                record.key == "product.product_pricelist_setting"
                and record.value == "advanced"
            ):
                raise ValidationError(_("Cannot delete this parameter"))
        return super().unlink()

    @api.constrains("key", "value")
    def check_value(self):
        if self.key == "product.product_pricelist_setting" and self.value != "advanced":
            raise ValidationError(
                _("The parameter Advanced price rules cannot be modified")
            )
