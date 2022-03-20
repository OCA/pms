import logging

from odoo import api, fields, models

CODE_SPAIN = "ES"

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    ine_code = fields.Char(
        string="INE State Code",
        compute="_compute_ine_code",
        store=True,
    )

    @api.depends("nationality_id", "residence_state_id")
    def _compute_ine_code(self):
        for record in self:
            if not record.nationality_id:
                record.ine_code = False
            elif record.nationality_id.code != CODE_SPAIN:
                record.ine_code = record.nationality_id.code_alpha3
            else:
                if not record.residence_state_id:
                    record.ine_code = False
                record.ine_code = record.residence_state_id.ine_code

    def _check_enought_invoice_data(self):
        self.ensure_one()
        res = super(ResPartner, self)._check_enought_invoice_data()
        if not res:
            return res
        if self.country_id.code == "ES":
            if not self.state_id and not self.zip:
                return False
        return True
