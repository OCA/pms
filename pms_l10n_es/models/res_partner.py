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

    @api.depends("nationality_id", "state_id")
    def _compute_ine_code(self):
        for record in self:
            if not record.nationality_id:
                record.ine_code = False
            elif record.nationality_id.code != CODE_SPAIN:
                record.ine_code = record.country_id.code_alpha3
            else:
                if not record.state_id:
                    record.ine_code = False
                record.ine_code = record.state_id.ine_code
