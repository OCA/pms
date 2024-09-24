from odoo import fields, models


class PmsCheckinPartner(models.Model):
    _inherit = "pms.checkin.partner"

    origin_input_data = fields.Selection(
        [
            ("wizard", "Wizard"),
            ("form", "Form"),
            ("regular_customer", "Regular Customer"),
            ("ocr", "OCR"),
            ("precheckin", "Precheckin"),
        ],
        string="Origin Input Data",
    )
