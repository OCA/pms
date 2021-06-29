# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ChannelWubookBinding(models.AbstractModel):
    _name = "channel.wubook.binding"
    _inherit = "channel.binding"

    # binding fields
    backend_id = fields.Many2one(
        comodel_name="channel.wubook.backend",
        string="Wubook Backend",
        required=True,
        readonly=True,
        ondelete="restrict",
    )
