# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PmsBoardService(models.Model):
    _inherit = "pms.board.service"

    channel_wubook_bind_ids = fields.One2many(
        comodel_name="channel.wubook.pms.board.service",
        inverse_name="odoo_id",
        string="Channel Wubook PMS Bindings",
    )
