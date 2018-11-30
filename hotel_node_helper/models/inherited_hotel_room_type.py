# Copyright 2018  Pablo Q. Barriuso
# Copyright 2018  Alexandre Díaz
# Copyright 2018  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class HotelRoomType(models.Model):

    _inherit = 'hotel.room.type'

    @api.model
    def get_room_type_availability(self, dfrom, dto, room_type_id):
        free_rooms = self.check_availability_room_type(dfrom, dto)
        availability_real = self.env['hotel.room'].search_count([
            ('id', 'in', free_rooms.ids),
            ('room_type_id', '=', room_type_id),
        ])
        availability_plan = self.env['hotel.room.type.availability'].search_read([
            ('date', '>=', dfrom),
            ('date', '<', dto),
            ('room_type_id', '=', room_type_id),
        ], ['avail']) or [{'avail': availability_real}]

        availability_plan = min([r['avail'] for r in availability_plan])

        return min(availability_real, availability_plan)

    @api.model
    def get_room_type_price_unit(self, dfrom, dto, room_type_id):
        # TODO review how to get the prices
        reservation_line_ids = self.env['hotel.reservation'].prepare_reservation_lines(
            dfrom,
            (fields.Date.from_string(dto) - fields.Date.from_string(dfrom)).days,
            {'room_type_id': room_type_id}
        )
        reservation_line_ids = reservation_line_ids['reservation_line_ids']
        # QUESTION Why add [[5, 0, 0], ¿?
        # del reservation_line_ids[0]

        return reservation_line_ids

    @api.model
    def get_room_type_restrictions(self, dfrom, dto, room_type_id):
        restrictions_plan = self.env['hotel.room.type.restriction.item'].search_read([
            ('date', '>=', dfrom),
            ('date', '<', dto),
            ('room_type_id', '=', room_type_id),
        ], ['min_stay']) or [{'min_stay': 0}]

        min_stay = max([r['min_stay'] for r in restrictions_plan])

        return min_stay

    @api.model
    def get_room_type_planning(self, dfrom, dto, room_type_id):
        availability = self.get_room_type_availability(dfrom, dto, room_type_id)

        price_unit = self.get_room_type_price_unit(dfrom, dto, room_type_id)

        restrictions = self.get_room_type_restrictions(dfrom, dto, room_type_id)

        return {'availability': availability, 'price_unit': price_unit, 'restrictions': restrictions}
