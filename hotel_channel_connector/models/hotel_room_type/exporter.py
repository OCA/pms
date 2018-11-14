# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo import api, _
_logger = logging.getLogger(__name__)

class HotelRoomTypeExporter(Component):
    _name = 'channel.hotel.room.type.exporter'
    _inherit = 'hotel.channel.exporter'
    _apply_on = ['channel.hotel.room.type']
    _usage = 'hotel.room.type.exporter'

    @api.model
    def modify_room(self, binding):
        try:
            return self.backend_adapter.modify_room(
                binding.external_id,
                binding.name,
                binding.ota_capacity,
                binding.list_price,
                binding.total_rooms_count,
                binding.channel_short_code)
        except ChannelConnectorError as err:
            self.create_issue(
                section='room',
                internal_message=str(err),
                channel_message=err.data['message'])

    @api.model
    def create_room(self, binding):
        seq_obj = self.env['ir.sequence']
        short_code = seq_obj.next_by_code('hotel.room.type')[:4]
        try:
            external_id = self.backend_adapter.create_room(
                short_code,
                binding.name,
                binding.ota_capacity,
                binding.list_price,
                binding.total_rooms_count
            )
        except ChannelConnectorError as err:
            self.create_issue(
                section='room',
                internal_message=str(err),
                channel_message=err.data['message'])
        else:
            binding.write({
                'external_id': external_id,
                'channel_short_code': short_code,
            })
            self.binder.bind(external_id, binding)
