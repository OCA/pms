# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo.addons.hotel_channel_connector_wubook.components.backend_adapter import (
    DEFAULT_WUBOOK_DATE_FORMAT)
from odoo import api, _, fields
_logger = logging.getLogger(__name__)


class HotelRoomTypeAvailabilityExporter(Component):
    _inherit = 'channel.hotel.room.type.availability.exporter'

    def push_availability(self):
        channel_hotel_room_type_obj = self.env['channel.hotel.room.type']
        channel_room_type_avail_ids = self.env['channel.hotel.room.type.availability'].search([
            ('backend_id', '=', self.backend_record.id),
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
                    date_dt = fields.Date.from_string(channel_room_type_avail.date)
                    days.append({
                        'date': date_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                        'avail': channel_room_type_avail.channel_avail,
                        'no_ota': channel_room_type_avail.no_ota and 1 or 0,
                        # 'booked': room_type_avail.booked and 1 or 0,
                    })
                room_type_bind = channel_hotel_room_type_obj.search([
                    ('odoo_id', '=', room_type.id),
                    ('backend_id', '=', self.backend_record.id),
                ], limit=1)
                avails.append({'id': room_type_bind.external_id, 'days': days})
        _logger.info("==[ODOO->CHANNEL]==== AVAILABILITY ==")
        _logger.info(avails)
        if any(avails):
            try:
                # For functions updating room values (like availability, prices, restrictions and so on),
                # for example update_avail(), there is a maximum number of updatable days (for __each room__)
                # depending on the time window.
                # Number of updated days    Time window (seconds)
                # 1460                      1
                # 4380                      180
                # 13140                     3600
                # 25550                     43200
                # 29200                     86400
                # 32850                     172800
                # 36500                     259200
                self.backend_adapter.update_availability(avails)
            except ChannelConnectorError as err:
                self.create_issue(
                    section='avail',
                    internal_message=str(err),
                    channel_message=err.data['message'])
                return False
            else:
                channel_room_type_avail_ids.with_context({
                    'connector_no_export': True,
                }).write({
                    'channel_pushed': True,
                    'sync_date': fields.Datetime.now(),
                })
        return True
