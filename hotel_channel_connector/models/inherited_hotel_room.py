# Copyright 2019 Pablo Q. Barriuso <pabloqb@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta
from odoo import models, api, fields
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class HotelRoom(models.Model):
    _inherit = 'hotel.room'

    @api.multi
    def write(self, vals):
        """
        Update default availability for segmentation management
        """
        if vals.get('room_type_id'):
            room_type_ids = []
            for record in self:
                room_type_ids.append({
                    'new_room_type_id': vals.get('room_type_id'),
                    'old_room_type_id': record.room_type_id.id,
                })

            res = super().write(vals)

            for item in room_type_ids:
                if item['new_room_type_id'] != item['old_room_type_id']:
                    old_channel_room_type = self.env['channel.hotel.room.type'].search([
                        ('odoo_id', '=', item['old_room_type_id'])
                    ])
                    old_channel_room_type._onchange_availability()
                    channel_availability = self.env['channel.hotel.room.type.availability'].search([
                        ('room_type_id', '=', item['old_room_type_id']),
                        '|',
                        ('quota', '>', old_channel_room_type.total_rooms_count),
                        ('max_avail', '>', old_channel_room_type.total_rooms_count),
                    ], order='date asc') or False
                    if channel_availability:
                        date_range = channel_availability.mapped('date')
                        dfrom = date_range[0]
                        dto = (fields.Date.from_string(date_range[-1]) + timedelta(days=1)).strftime(
                            DEFAULT_SERVER_DATE_FORMAT)
                        self.env['channel.hotel.room.type.availability'].refresh_availability(
                            checkin=dfrom,
                            checkout=dto,
                            backend_id=1,
                            room_type_id=item['old_room_type_id'],)

                    new_channel_room_type = self.env['channel.hotel.room.type'].search([
                        ('odoo_id', '=', item['new_room_type_id'])
                    ])
                    new_channel_room_type._onchange_availability()
                    channel_availability = self.env['channel.hotel.room.type.availability'].search([
                        ('room_type_id', '=', item['new_room_type_id']),
                        '|',
                        ('quota', '>', new_channel_room_type.total_rooms_count),
                        ('max_avail', '>', new_channel_room_type.total_rooms_count),
                    ], order='date asc') or False
                    if channel_availability:
                        date_range = channel_availability.mapped('date')
                        dfrom = date_range[0]
                        dto = (fields.Date.from_string(date_range[-1]) + timedelta(days=1)).strftime(
                            DEFAULT_SERVER_DATE_FORMAT)
                        self.env['channel.hotel.room.type.availability'].refresh_availability(
                            checkin=dfrom,
                            checkout=dto,
                            backend_id=1,
                            room_type_id=item['new_room_type_id'], )
        else:
            res = super().write(vals)
        return res
