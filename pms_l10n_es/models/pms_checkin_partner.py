import logging

from odoo import api, fields, models

CODE_SPAIN = "ES"

_logger = logging.getLogger(__name__)


class PmsCheckinPartner(models.Model):
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
                if record.partner_id.id_numbers:
                    dni_numbers = record.partner_id.id_numbers.filtered(
                        lambda x: x.category_id.name == "DNI"
                    )
                    if len(dni_numbers) == 1 and dni_numbers.support_number:
                        record.support_number = dni_numbers.support_number
                    else:
                        record.support_number = False
                else:
                    record.support_number = False

    @api.model
    def _checkin_mandatory_fields(self, country=False, depends=False):
        mandatory_fields = super(PmsCheckinPartner, self)._checkin_mandatory_fields(
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
            mandatory_fields.extend(
                [
                    "residence_state_id",
                    "residence_street",
                    "residence_city",
                ]
            )
        return mandatory_fields

    @api.model
    def _checkin_manual_fields(self, country=False, depends=False):
        manual_fields = super(PmsCheckinPartner, self)._checkin_manual_fields(depends)
        manual_fields.extend(["support_number"])
        return manual_fields

    def _get_partner_by_document(self, document_number, document_type):
        # if not find partner by documents (super method) then search by
        # partner fields, VAT, or aeat_identification equivalent
        partner = super(PmsCheckinPartner, self)._get_partner_by_document(
            document_number, document_type
        )
        if not partner and document_number and document_type:
            if document_type.aeat_identification_type in ["03", "05", "06"]:
                search_field_name = "aeat_identification"
                search_comparison = "="
            elif document_type.aeat_identification_type in ["02", "04"]:
                search_field_name = "vat"
                search_comparison = "ilike"
            if search_field_name:
                partner = self.env["res.partner"].search(
                    [(search_field_name, search_comparison, document_number)], limit=1
                )
        return partner
