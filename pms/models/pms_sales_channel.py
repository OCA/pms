from odoo import models, fields
class PmsSalesChannel(models.Model):
    _name="pms.room.sales.channel"
    _description="Sales Channel"
    _order="sequence, channel_type, name"

    name=fields.Char("Sale Channel Name", required=True)
    channel_type=field.Selection(
        selection=[
            ("direct","Direct"),
            ("indirect","Indirect"),
        ],
        string="Type"
    )
    is_offline=fields.Boolean("Is Offline")
    is_online=fields.Boolean("Is Online")
