# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import date, timedelta
from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo.addons.connector.components.mapper import mapping, only_create
from odoo import api, fields, _
_logger = logging.getLogger(__name__)


class HotelRoomTypeAvailabilityImporter(Component):
    _inherit = 'channel.hotel.room.type.availability.importer'

    @api.model
    def import_availability_values(self, date_from, date_to):
        now_dt = date.today()
        dfrom_dt = fields.Date.from_string(date_from)
        dto_dt = fields.Date.from_string(date_to)
        if dfrom_dt < now_dt:
            dfrom_dt = now_dt
        if dfrom_dt > dto_dt:
            dfrom_dt, dto_dt = dto_dt, dfrom_dt
        if dto_dt < now_dt:
            return True

        count = 0
        try:
            results = self.backend_adapter.fetch_rooms_values(date_from, date_to)
        except ChannelConnectorError as err:
            self.create_issue(
                section='avail',
                internal_message=str(err),
                channel_message=err.data['message'],
                dfrom=date_from, dto=date_to)
        else:
            _logger.info("==[CHANNEL->ODOO]==== AVAILABILITY (%s - %s) ==",
                         date_from, date_to)
            _logger.info(results)

            channel_room_type_avail_obj = self.env['channel.hotel.room.type.availability']
            channel_room_type_obj = self.env['channel.hotel.room.type']
            room_avail_mapper = self.component(
                usage='import.mapper',
                model_name='channel.hotel.room.type.availability')
            for room_k, room_v in results.items():
                iter_day = dfrom_dt
                channel_room_type = channel_room_type_obj.search([
                    ('backend_id', '=', self.backend_record.id),
                    ('external_id', '=', room_k)
                ], limit=1)
                if channel_room_type:
                    for room in room_v:
                        room.update({
                            'room_type_id': channel_room_type.odoo_id.id,
                            'date': fields.Date.to_string(iter_day),
                        })
                        map_record = room_avail_mapper.map_record(room)
                        room_type_avail_bind = channel_room_type_avail_obj.search([
                            ('backend_id', '=', self.backend_record.id),
                            ('room_type_id', '=', room['room_type_id']),
                            ('date', '=', room['date'])
                        ], limit=1)
                        if room_type_avail_bind:
                            if room_type_avail_bind.channel_avail != room['avail']:
                                room_type_avail_bind.with_context({
                                    'connector_no_export': True,
                                }).write({'channel_pushed': False})
                                self.create_issue(
                                    section='avail',
                                    dfrom=room['date'], dto=room['date'],
                                    internal_message=_(
                                        "Channel try to change availiability! \
                                        Updating channel values for Room Type %s... \
                                        (Odoo: %d -- Channel: %d)" % (
                                            room_type_avail_bind.room_type_id.name,
                                            room['avail'],
                                            room_type_avail_bind.channel_avail)))
                        else:
                            room_type_avail_bind = channel_room_type_avail_obj.with_context({
                                'connector_no_export': True,
                            }).create(map_record.values(for_create=True))
                        room_type_avail_bind.channel_pushed = True
                        iter_day += timedelta(days=1)
                count = count + 1
        return count


class HotelRoomTypeAvailabilityImportMapper(Component):
    _name = 'channel.hotel.room.type.availability.import.mapper'
    _inherit = 'channel.import.mapper'
    _apply_on = 'channel.hotel.room.type.availability'

    direct = [
        ('no_ota', 'no_ota'),
        ('booked', 'booked'),
        ('avail', 'channel_avail'),
        ('avail', 'quota'),
        ('date', 'date'),
    ]

    @only_create
    @mapping
    def channel_pushed(self, record):
        return {'channel_pushed': True}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def room_type_id(self, record):
        return {'room_type_id': record['room_type_id']}

    @mapping
    def sync_date(self, record):
        return {'sync_date': fields.Datetime.now()}
