from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    document_type = fields.Selection(
        [
            ("D", "DNI"),
            ("P", "Passport"),
            ("C", "Driving License"),
            ("I", "Identification Document"),
            ("N", "Spanish residence permit"),
            ("X", "European residence permit"),
        ],
        help="Select a valid document type",
        string="Doc. type",
    )
    document_number = fields.Char(
        string="Document number",
    )
    document_expedition_date = fields.Date(string="Document expedition date")

    @api.constrains("document_number", "document_type")
    def _check_document(self):
        for record in self.filtered("document_number"):
            if not record.document_type:
                raise models.ValidationError(_("Document Type field are mandatory"))
            partner = self.search(
                [
                    ("document_number", "=", record.document_number),
                    ("document_type", "=", record.document_type),
                    ("id", "!=", record.id),
                ]
            )
            if partner:
                raise models.ValidationError(
                    _(
                        "Document Number Partner %s already exist (%s)",
                        record.document_number,
                        partner.name,
                    )
                )

    @api.model
    def _get_key_fields(self):
        key_fields = super(ResPartner, self)._get_key_fields()
        key_fields.extend(["document_number"])
        return key_fields
