from odoo import api, fields, models


class PmsCheckinPartner(models.Model):
    _inherit = "pms.checkin.partner"

    lastname2 = fields.Char("Last Name", related="partner_id.lastname2")
    birthdate_date = fields.Date("Birthdate", related="partner_id.birthdate_date")
    document_number = fields.Char(
        "Document Number", related="partner_id.document_number"
    )
    document_type = fields.Selection(
        "Document Type", related="partner_id.document_type"
    )
    document_expedition_date = fields.Date(
        "Expedition Date", related="partner_id.document_expedition_date"
    )
    gender = fields.Selection("Gender", related="partner_id.gender")

    @api.model
    def _checkin_mandatory_fields(self, depends=False):
        mandatory_fields = super(PmsCheckinPartner, self)._checkin_mandatory_fields(
            depends
        )
        mandatory_fields.extend(
            [
                "lastname2",
                "birthdate_date",
                "document_number",
                "document_type",
                "document_expedition_date",
                "gender",
            ]
        )
        return mandatory_fields
