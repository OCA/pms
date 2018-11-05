# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo import api, fields, _
from odoo.addons.hotel_channel_connector.components.backend_adapter import (
    DEFAULT_WUBOOK_DATE_FORMAT)
_logger = logging.getLogger(__name__)

class HotelRoomTypeAvailabilityExporter(Component):
    _name = 'channel.hotel.room.type.availability.exporter'
    _inherit = 'hotel.channel.exporter'
    _apply_on = ['channel.hotel.room.type.availability']
    _usage = 'hotel.room.type.availability.exporter'

    @api.model
    def update_availability(self, binding):
        if any(binding.room_type_id.channel_bind_ids):
            try:
                sday_dt = fields.Date.from_string(binding.date)
                # Supossed that only exists one channel connector per record
                binding.channel_pushed = True
                return self.backend_adapter.update_availability({
                    'id': binding.room_type_id.channel_bind_ids[0].channel_room_id,
                    'days': [{
                        'date': sday_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                        'avail': binding.avail,
                        'no_ota': binding.no_ota,
                    }],
                })
            except ChannelConnectorError as err:
                self.create_issue(
                    backend=self.backend_adapter.id,
                    section='avail',
                    internal_message=_("Can't update availability in WuBook"),
                    channel_message=err.data['message'])

    def push_availability(self):
        channel_room_type_avail_ids = self.env['channel.hotel.room.type.availability'].search([
            ('channel_pushed', '=', False),
            ('date', '>=', fields.Date.today())
        ])
        room_types = channel_room_type_avail_ids.mapped('room_type_id')
        avails = []
        for room_type in room_types:
            if any(room_type.channel_bind_ids):
                channel_room_type_avails = channel_room_type_avail_ids.filtered(
                    lambda x: x.room_type_id.id == room_type.id)
                days = []
                for channel_room_type_avail in channel_room_type_avails:
                    channel_room_type_avail.channel_pushed = True
                    cavail = channel_room_type_avail.avail
                    if channel_room_type_avail.channel_max_avail >= 0 and \
                            cavail > channel_room_type_avail.channel_max_avail:
                        cavail = channel_room_type_avail.channel_max_avail
                    date_dt = fields.Date.from_string(channel_room_type_avail.date)
                    days.append({
                        'date': date_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                        'avail': cavail,
                        'no_ota': channel_room_type_avail.no_ota and 1 or 0,
                        # 'booked': room_type_avail.booked and 1 or 0,
                    })
                avails.append({'id': room_type.channel_bind_ids[0].channel_room_id, 'days': days})
        _logger.info("UPDATING AVAILABILITY IN WUBOOK...")
        _logger.info(avails)
        if any(avails):
            try:
                self.backend_adapter.update_availability(avails)
            except ChannelConnectorError as err:
                self.create_issue(
                    backend=self.backend_adapter.id,
                    section='avail',
                    internal_message=_("Can't update availability in WuBook"),
                    channel_message=err.data['message'])
