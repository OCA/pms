# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PmsRoomType(models.Model):
    _inherit = "pms.room.type"

    channel_wubook_bind_ids = fields.One2many(
        comodel_name="channel.wubook.pms.room.type",
        inverse_name="odoo_id",
        string="Channel Wubook PMS Bindings",
    )

    # def get_binding(self, backend):
    #     self.ensure_one()
    #     return self.channel_wubook_bind_ids.filtered(
    #         lambda x: x.backend_id == backend
    #     )
