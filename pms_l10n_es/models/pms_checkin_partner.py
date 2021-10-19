import logging

from odoo import api, models

CODE_SPAIN = "ES"

_logger = logging.getLogger(__name__)


class PmsCheckinParnert(models.Model):
    _inherit = "pms.checkin.partner"

    @api.model
    def _checkin_mandatory_fields(self, country=False, depends=False):
        mandatory_fields = super(PmsCheckinParnert, self)._checkin_mandatory_fields(
            depends
        )
        mandatory_fields.extend(
            [
                "birthdate_date",
                "gender",
                "document_number",
                "document_type",
                "document_expedition_date",
                "nationality_id",
            ]
        )
        if depends or (country and country.code == CODE_SPAIN):
            mandatory_fields.append("state_id")
        return mandatory_fields
