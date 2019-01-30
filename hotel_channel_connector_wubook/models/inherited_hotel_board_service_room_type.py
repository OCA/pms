# Copyright 2019 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class HotelBoardServiceRoomType(models.Model):

    _inherit = 'hotel.board.service.room.type'

    channel_service = fields.Selection(selection_add=[
        ('nb', 'No Board'),
        ('fb', 'Full Board'),
        ('hb', 'Half Board'),
        ('bb', 'Breakfast Only'),
        ('ai', 'All Inclusive')
    ])
