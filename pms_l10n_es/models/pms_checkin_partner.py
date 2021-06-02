from odoo import api, fields, models


class PmsCheckinPartner(models.Model):
    _inherit = "pms.checkin.partner"

    lastname2 = fields.Char(
        required=True,
    )
