from odoo import fields, models


class PmsCheckinPartner(models.Model):
    _inherit = "pms.checkin.partner"

    origin_input_data = fields.Selection(
        [
            ("wizard", "Wizard"),
            ("wizard-precheckin", "Wizard-Precheckin"),
            ("form", "Form"),
            ("regular_customer", "Regular Customer"),
            ("ocr", "OCR"),
            ("ocr-precheckin", "OCR-Precheckin"),
            ("precheckin", "Precheckin"),
        ],
        string="Origin Input Data",
    )
