from odoo import fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    is_used_regula = fields.Boolean(
        string="Used regula", help="True if this property uses regula's OCR"
    )
