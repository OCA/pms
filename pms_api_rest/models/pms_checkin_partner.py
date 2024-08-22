import uuid

from odoo import api, fields, models
from odoo.tools.safe_eval import time


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
