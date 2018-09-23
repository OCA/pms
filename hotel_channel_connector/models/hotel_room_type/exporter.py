# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo import api, _

class HotelRoomTypeExporter(Component):
    _name = 'channel.hotel.room.type.exporter'
    _inherit = 'hotel.channel.exporter'
    _apply_on = ['channel.hotel.room.type']
    _usage = 'hotel.room.type.exporter'

    @api.model
    def modify_room(self, binding):
        try:
            return self.backend_adapter.modify_room(
                binding.channel_room_id,
                binding.name,
                binding.ota_capacity,
                binding.list_price,
                binding.total_rooms_count,
                binding.channel_short_code)
        except ChannelConnectorError as err:
            self.create_issue('room', _("Can't modify rooms in WuBook"), err.data['message'])

    @api.model
    def delete_room(self, binding):
        try:
            return self.backend_adapter.delete_room(binding.channel_room_id)
        except ChannelConnectorError as err:
            self.create_issue('room', _("Can't delete room in WuBook"), err.data['message'])

    @api.model
    def create_room(self, binding):
        try:
            seq_obj = self.env['ir.sequence']
            short_code = seq_obj.next_by_code('hotel.room.type')[:4]
            external_id = self.backend_adapter.create_room(
                short_code,
                binding.name,
                binding.ota_capacity,
                binding.list_price,
                binding.total_rooms_count
            )
            binding.write({
                'channel_room_id': external_id,
                'channel_short_code': short_code,
            })
        except ChannelConnectorError as err:
            self.create_issue('room', _("Can't delete room in WuBook"), err.data['message'])
        else:
            self.binder.bind(external_id, binding)
