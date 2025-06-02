from odoo import api, models
from odoo.tools.misc import str2bool


class PmsAvailability(models.Model):
    _inherit = "pms.availability"

    @api.model
    def apply_internal_availability_rules(self):
        param = self.env["ir.config_parameter"].get_param(
            "apply_internal_availability_rules", "False"
        )
        try:
            return str2bool(param)
        except Exception:
            return False
