from odoo import fields, models


class PmsTourismClassification(models.Model):
    _name = "pms.tourism.classification"
    _description = "Spanish Tourism Classification"

    name = fields.Char(
        required=True,
        help="Spanish tourism classification.",
    )
    description = fields.Text(
        help="Description of the Spanish tourism classification.",
    )
    code = fields.Char(
        required=True,
        help="Code of the Spanish tourism classification.",
    )
