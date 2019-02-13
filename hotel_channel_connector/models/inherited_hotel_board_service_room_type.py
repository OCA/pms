# Copyright 2019 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class HotelBoardServiceRoomType(models.Model):

    _inherit = 'hotel.board.service.room.type'

    channel_service = fields.Selection([], string='Channel Board Service')

    _sql_constraints = [
        ('room_type_channel_service_id_uniq', 'unique(hotel_room_type_id, channel_service)',
         'The channel board service must be unique for room type.'),
    ]