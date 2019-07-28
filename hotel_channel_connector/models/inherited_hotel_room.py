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

                    tz_hotel = self.env['ir.default'].sudo().get(
                        'res.config.settings', 'tz_hotel')
                    _today = fields.Date.context_today(self.with_context(tz=tz_hotel))

                    # update old room type values
                    old_channel_room_type = self.env['channel.hotel.room.type'].search([
                        ('odoo_id', '=', item['old_room_type_id'])
                    ])

                    old_room_type_total_rooms_count = old_channel_room_type.total_rooms_count

                    if old_channel_room_type.default_quota > old_room_type_total_rooms_count:
                        old_channel_room_type.default_quota = old_room_type_total_rooms_count

                    if old_channel_room_type.default_max_avail > old_room_type_total_rooms_count:
                        old_channel_room_type.default_max_avail = old_room_type_total_rooms_count

                    if old_channel_room_type.ota_capacity > old_channel_room_type.capacity:
                        old_channel_room_type.ota_capacity = old_channel_room_type.odoo_id.get_capacity()
                        issue_backend_id = old_channel_room_type.backend_id.id
                        issue_internal_message = "OTA capacity updated to %d for Room Type %s." % (
                                old_channel_room_type.ota_capacity,
                                old_channel_room_type.name)
                        issue_channel_object_id = old_channel_room_type.external_id

                        self.env['hotel.channel.connector.issue'].create({
                            'backend_id': issue_backend_id,
                            'section': 'room',
                            'internal_message': issue_internal_message,
                            'channel_object_id': issue_channel_object_id,
                        })

                    channel_availability = self.env['channel.hotel.room.type.availability'].search([
                        ('room_type_id', '=', item['old_room_type_id']),
                        ('channel_avail', '>', old_room_type_total_rooms_count),
                        ('date', '>=', _today)
                    ], order='date asc') or False
                    if channel_availability:
                        date_range = channel_availability.mapped('date')
                        dfrom = date_range[0]
                        dto = (fields.Date.from_string(date_range[-1]) + timedelta(days=1)).strftime(
                            DEFAULT_SERVER_DATE_FORMAT)

                        self.env['channel.hotel.room.type.availability'].refresh_availability(
                            checkin=dfrom,
                            checkout=dto,
                            backend_id=old_channel_room_type.backend_id.id,
                            room_type_id=item['old_room_type_id'],)

                    # updates new room type values
                    new_channel_room_type = self.env['channel.hotel.room.type'].search([
                        ('odoo_id', '=', item['new_room_type_id'])
                    ])

                    new_room_type_total_rooms_count = new_channel_room_type.total_rooms_count

                    if new_channel_room_type.default_quota > new_room_type_total_rooms_count:
                        new_channel_room_type.default_quota = new_room_type_total_rooms_count

                    if new_channel_room_type.default_max_avail > new_room_type_total_rooms_count:
                        new_channel_room_type.default_max_avail = new_room_type_total_rooms_count

                    if new_channel_room_type.ota_capacity > new_channel_room_type.capacity:
                        new_channel_room_type.ota_capacity = new_channel_room_type.odoo_id.get_capacity()
                        issue_backend_id = new_channel_room_type.backend_id.id
                        issue_internal_message = "OTA capacity updated to %d for Room Type %s." % (
                                new_channel_room_type.ota_capacity,
                                new_channel_room_type.name)
                        issue_channel_object_id = new_channel_room_type.external_id

                        self.env['hotel.channel.connector.issue'].create({
                            'backend_id': issue_backend_id,
                            'section': 'room',
                            'internal_message': issue_internal_message,
                            'channel_object_id': issue_channel_object_id,
                        })

                    channel_availability = self.env['channel.hotel.room.type.availability'].search([
                        ('room_type_id', '=', item['new_room_type_id']),
                        ('channel_avail', '>', new_room_type_total_rooms_count),
                        ('date', '>=', _today)
                    ], order='date asc') or False
                    if channel_availability:
                        date_range = channel_availability.mapped('date')
                        dfrom = date_range[0]
                        dto = (fields.Date.from_string(date_range[-1]) + timedelta(days=1)).strftime(
                            DEFAULT_SERVER_DATE_FORMAT)
                        self.env['channel.hotel.room.type.availability'].refresh_availability(
                            checkin=dfrom,
                            checkout=dto,
                            backend_id=new_channel_room_type.backend_id.id,
                            room_type_id=item['new_room_type_id'], )
            # TODO: channel_backend MUST be the same for both room types
            channel_backend = self.env['channel.hotel.room.type'].search([
                ('odoo_id', '=', vals.get('room_type_id'))
            ]).backend_id
            channel_backend.channel_availability_watchdog()
        else:
            res = super().write(vals)
        return res
