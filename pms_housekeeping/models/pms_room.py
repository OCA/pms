from odoo import fields, models


class PmsRoom(models.Model):
    _inherit = "pms.room"

    housekeeping_state = fields.Selection(
        selection=[
            ("dirty", "Dirty"),
            ("to_inspect", "To Inspect"),
            ("clean", "Clean"),
        ],
        string="Housekeeping State",
        required=True,
        default="dirty",
    )
