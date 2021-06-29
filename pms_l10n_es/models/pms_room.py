from odoo import fields, models


class PmsRoom(models.Model):
    _inherit = "pms.room"
    in_ine = fields.Boolean(
        string="In INE",
        help="Take it into account to generate INE statistics",
        default=True,
    )
