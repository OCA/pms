# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models

_log = logging.getLogger(__name__)


class PmsRoom(models.Model):
    _inherit = "pms.room"

    qty_double_bed = fields.Integer(string="Double Bed", default=0)
    qty_queen_bed = fields.Integer(string="Queen Bed", default=0)
    qty_king_bed = fields.Integer(string="King Bed", default=0)

    capacity = fields.Integer(string="Capacity", default=0, compute="_compute_capacity")

    @api.depends("qty_double_bed", "qty_queen_bed", "qty_king_bed")
    def _compute_capacity(self):
        for room in self:
            room.capacity = (
                (room.qty_double_bed * 2)
                + (room.qty_queen_bed * 2)
                + (room.qty_king_bed * 2)
            )
