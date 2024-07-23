import uuid

from odoo import api, fields, models
from odoo.tools.safe_eval import time


class PmsFolio(models.Model):
    _inherit = "pms.folio"
    api_rest_id = fields.Char(string="API Rest ID", help="API Rest ID")

    pms_api_log_ids = fields.Many2many(
        string="API Logs",
        help="API Logs",
        comodel_name="pms.api.log",
        relation="pms_folio_pms_api_log_rel",
        column1="folio_ids",
        column2="pms_api_log_ids",
    )

    @api.model
    def create(self, vals):
        result = super(PmsFolio, self).create(vals)
        if not result.api_rest_id:
            self._generate_api_rest_id(result)
        return result

    @api.model
    def _generate_api_rest_id(self, folio_record):
        if not folio_record.api_rest_id:
            timestamp = int(time.time() * 1000)
            new_uuid = uuid.uuid4()
            unique_uuid = f"{new_uuid}_{timestamp}"
            folio_record.api_rest_id = unique_uuid
