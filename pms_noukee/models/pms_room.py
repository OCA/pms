from odoo import fields, models


class PmsRoom(models.Model):

    _inherit = "pms.room"

    door_ids = fields.One2many(
        comodel_name="pms.door", string="Door Ids", inverse_name="room_id"
    )
