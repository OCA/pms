# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ChannelWubookPmsRoomTypeBoardServiceBinding(models.AbstractModel):
    _name = "channel.wubook.pms.room.type.board.service"
    _inherit = "channel.wubook.binding"
    _inherits = {"pms.board.service.room.type": "odoo_id"}

    odoo_id = fields.Many2one(
        comodel_name="pms.board.service.room.type",
        string="Odoo ID",
        required=True,
        ondelete="cascade",
    )
