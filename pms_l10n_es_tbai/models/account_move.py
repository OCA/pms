from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _is_l10n_es_tbai_simplified(self):
        if self.commercial_partner_id == self.env.ref("pms.various_pms_partner"):
            return True
        return super()._is_l10n_es_tbai_simplified()
