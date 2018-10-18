# Copyright 2018  Pablo Q. Barriuso
# Copyright 2018  Alexandre Díaz
# Copyright 2018  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import wdb
from odoo import models, fields, api


class HotelRoomType(models.Model):

    _inherit = 'hotel.room.type'

    @api.model
    def check_availability_room_ids(self, dfrom, dto,
                                room_type_id=False, notthis=[]):
        """
        Check availability for all or specific room types between dates
        @return: A list of `ids` with free rooms
        """
        free_rooms = super().check_availability_room(dfrom, dto, room_type_id, notthis)
        return free_rooms.ids
