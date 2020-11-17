from odoo import fields, models


class PmsSaleChannel(models.Model):
    _name = "pms.sale.channel"
    _description = "Sales Channel"

    # Fields declaration
    name = fields.Text(string="Sale Channel Name")
    channel_type = fields.Selection(
        [("direct", "Direct"), ("indirect", "Indirect")], string="Sale Channel Type"
    )
