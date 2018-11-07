# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta
from odoo.exceptions import ValidationError
from odoo.addons.component.core import Component
from odoo.addons.sconnector.components.mapper import mapping
from odoo import fields, api, _
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
from odoo.addons.hotel_channel_connector.components.backend_adapter import DEFAULT_WUBOOK_DATE_FORMAT
_logger = logging.getLogger(__name__)


class HotelRoomTypeImporter(Component):
    _name = 'channel.hotel.room.type.importer'
    _inherit = 'hotel.channel.importer'
    _apply_on = ['channel.hotel.room.type']
    _usage = 'hotel.room.type.importer'

    @api.model
    def get_rooms(self):
        results = self.backend_adapter.fetch_rooms()

        channel_room_type_obj = self.env['channel.hotel.room.type']
        room_mapper = self.component(usage='import.mapper',
                                     model_name='channel.hotel.room.type')
        count = len(results)
        for room in results:
            map_record = room_mapper.map_record(room)
            room_bind = channel_room_type_obj.search([
                ('external_id', '=', room['id'])
            ], limit=1)
            if room_bind:
                room_bind.with_context({'wubook_action': False}).write(map_record.values())
            else:
                room_bind = channel_room_type_obj.with_context({'wubook_action': False}).create(
                    map_record.values(for_create=True))
        return count

    @api.model
    def fetch_rooms_values(self, dfrom, dto, rooms=False,
                           set_max_avail=False):
        # Sanitize Dates
        now_dt = fields.Datetime.now()
        dfrom_dt = fields.Date.from_string(dfrom)
        dto_dt = fields.Date.from_string(dto)
        if dto_dt < now_dt:
            return True
        if dfrom_dt < now_dt:
            dfrom_dt = now_dt
        if dfrom_dt > dto_dt:
            dfrom_dt, dto_dt = dto_dt, dfrom_dt

        results = self.backend_adapter.fetch_rooms_values(
            dfrom_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            dto_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            rooms)
        self._generate_room_values(dfrom, dto, results,
                                   set_max_avail=set_max_avail)

    @api.model
    def _map_room_values_availability(self, day_vals, set_max_avail):
        channel_room_type_avail_obj = self.env['channel.hotel.room.type.availability']
        room_avail_mapper = self.component(usage='import.mapper',
                                           model_name='channel.hotel.room.type.availability')
        map_record = room_avail_mapper.map_record(day_vals)
        map_record.update(channel_pushed=True)
        if set_max_avail:
            map_record.update(max_avail=day_vals.get('avail', 0))

        channel_room_type_avail = channel_room_type_avail_obj.search([
            ('room_type_id', '=', day_vals['room_type_id']),
            ('date', '=', day_vals['date'])
        ], limit=1)
        if channel_room_type_avail:
            channel_room_type_avail.with_context({
                'wubook_action': False,
            }).write(map_record.values())
        else:
            channel_room_type_avail_obj.with_context({
                'wubook_action': False,
                'mail_create_nosubscribe': True,
            }).create(map_record.values(for_create=True))

    @api.model
    def _map_room_values_restrictions(self, day_vals):
        channel_room_type_restr_item_obj = self.env['channel.hotel.room.type.restriction.item']
        room_restriction_mapper = self.component(
            usage='import.mapper',
            model_name='channel.hotel.room.type.restriction.item')
        map_record = room_restriction_mapper.map_record(day_vals)
        map_record.update(channel_pushed=True)

        room_type_restr = channel_room_type_restr_item_obj.search([
            ('room_type_id', '=', day_vals['room_type_id']),
            ('applied_on', '=', '0_room_type'),
            ('date', '=', day_vals['date']),
            ('restriction_id', '=', day_vals['restriction_plan_id']),
        ])
        if room_type_restr:
            room_type_restr.with_context({
                'wubook_action': False,
            }).write(map_record.values())
        else:
            channel_room_type_restr_item_obj.with_context({
                'wubook_action': False,
            }).create(map_record.values(for_create=True))

    @api.model
    def _generate_room_values(self, dfrom, dto, values, set_max_avail=False):
        channel_room_type_restr_obj = self.env['channel.hotel.room.type.restriction']
        channel_hotel_room_type_obj = self.env['channel.hotel.room.type']
        def_restr_plan = channel_room_type_restr_obj.search([('channel_plan_id', '=', '0')])
        _logger.info("==== ROOM VALUES (%s -- %s)", dfrom, dto)
        _logger.info(values)
        for k_rid, v_rid in values.iteritems():
            room_type = channel_hotel_room_type_obj.search([
                ('channel_plan_id', '=', k_rid)
            ], limit=1)
            if room_type:
                date_dt = fields.Date.from_string(
                    dfrom,
                    dtformat=DEFAULT_WUBOOK_DATE_FORMAT)
                for day_vals in v_rid:
                    date_str = date_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    day_vals.update({
                        'room_type_id': room_type.odoo_id.id,
                        'date': date_str,
                    })
                    self._map_room_values_availability(day_vals, set_max_avail)
                    if def_restr_plan:
                        day_vals.update({
                            'restriction_plan_id': def_restr_plan.odoo_id.id
                        })
                        self._map_room_values_restrictions(day_vals)
                    date_dt = date_dt + timedelta(days=1)
        return True

class HotelRoomTypeImportMapper(Component):
    _name = 'channel.hotel.room.type.import.mapper'
    _inherit = 'channel.import.mapper'
    _apply_on = 'channel.hotel.room.type'

    direct = [
        ('id', 'external_id'),
        ('shortname', 'channel_short_code'),
        ('occupancy', 'ota_capacity'),
        ('price', 'list_price'),
        ('name', 'name'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}
