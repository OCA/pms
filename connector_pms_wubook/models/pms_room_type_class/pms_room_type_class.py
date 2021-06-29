# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PmsRoomTypeClass(models.Model):
    _inherit = "pms.room.type.class"

    channel_wubook_bind_ids = fields.One2many(
        comodel_name="channel.wubook.pms.room.type.class",
        inverse_name="odoo_id",
        string="Channel Wubook PMS Bindings",
    )
