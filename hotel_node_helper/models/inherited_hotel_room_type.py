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

    @api.model
    def get_room_type_availability(self, dfrom, dto, room_type_id):
        free_rooms = self.check_availability_room(dfrom, dto)
        availability_real = self.env['hotel.room'].search_count([
            ('id', 'in', free_rooms.ids),
            ('room_type_id', '=', room_type_id),
        ])
        availability_plan = self.env['hotel.room.type.availability'].search_read([
            ('date', '>=', dfrom),
            ('date', '<', dto),
            ('room_type_id', '=', room_type_id),

        ], ['avail']) or float('inf')

        if isinstance(availability_plan, list):
            availability_plan = min([r['avail'] for r in availability_plan])

        return min(availability_real, availability_plan)
