from odoo import fields, models


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
