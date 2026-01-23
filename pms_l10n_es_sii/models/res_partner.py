from odoo import _, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    def unlink(self):
        various_partner = self.env.ref("pms.various_pms_partner")
        if various_partner.id in self.ids:
            raise ValidationError(
                _("The partner %s cannot be deleted"), various_partner.name
            )
        return super().unlink()
