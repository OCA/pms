# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ChannelWubookPmsRoomTypeClassBinding(models.Model):
    _name = "channel.wubook.pms.room.type.class"
    _inherit = "channel.wubook.binding"
    _inherits = {"pms.room.type.class": "odoo_id"}

    # binding fields
    odoo_id = fields.Many2one(
        comodel_name="pms.room.type.class",
        string="Odoo ID",
        required=True,
        ondelete="cascade",
    )
