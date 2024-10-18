from odoo import fields, models


class PmsRoomTypeClass(models.Model):
    _inherit = "pms.room.type.class"

    icon_pms_api_rest = fields.Image(
        string="Icon room type class image",
        store=True,
    )
