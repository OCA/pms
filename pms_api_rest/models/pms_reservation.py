import uuid

from odoo import api, fields, models
from odoo.tools.safe_eval import time


class PmsReservation(models.Model):
    _inherit = "pms.reservation"
    api_rest_id = fields.Char(string="API Rest ID", help="API Rest ID")

    @api.model
    def create(self, vals):
        result = super(PmsReservation, self).create(vals)
        self._generate_api_rest_id(result)
        result.access_token = result._portal_ensure_token()
        return result

    @api.model
    def _generate_api_rest_id(self, reservation_record):
        if not reservation_record.api_rest_id:
            timestamp = int(time.time() * 1000)
            new_uuid = uuid.uuid4()
            unique_uuid = f"{new_uuid}_{timestamp}"
            reservation_record.api_rest_id = unique_uuid
