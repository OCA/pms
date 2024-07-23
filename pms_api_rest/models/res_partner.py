import time
import uuid

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"
    api_rest_id = fields.Char(string="API Rest ID", help="API Rest ID")

    @api.model
    def create(self, vals):
        result = super(ResPartner, self).create(vals)
        if not result.api_rest_id:
            self._generate_api_rest_id(result)
        return result

    @api.model
    def _generate_api_rest_id(self, partner_record):
        if not partner_record.api_rest_id:
            timestamp = int(time.time() * 1000)
            new_uuid = uuid.uuid4()
            unique_uuid = f"{new_uuid}_{timestamp}"
            partner_record.api_rest_id = unique_uuid
