import logging

from odoo import api, fields, models

CODE_SPAIN = "ES"

_logger = logging.getLogger(__name__)


class PmsCheckinParnert(models.Model):
    _inherit = "pms.checkin.partner"

    support_number = fields.Char(
        string="Support number",
        help="ID support number",
        readonly=False,
        store=True,
        compute="_compute_support_number",
    )

    @api.depends("partner_id")
    def _compute_support_number(self):
        for record in self:
            if not record.support_number:
                if (
                    record.partner_id.id_numbers
                    and record.partner_id.id_numbers[0].support_number
                ):
                    record.support_number = record.partner_id.id_numbers[
                        0
                    ].support_number

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
