# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo import api, _
_logger = logging.getLogger(__name__)

class HotelRoomTypeRestrictionExporter(Component):
    _name = 'channel.hotel.room.type.restriction.exporter'
    _inherit = 'hotel.channel.exporter'
    _apply_on = ['channel.hotel.room.type.restriction']
    _usage = 'hotel.room.type.restriction.exporter'

    @api.model
    def rename_rplan(self, binding):
        try:
            return self.backend_adapter.rename_rplan(
                binding.external_id,
                binding.name)
        except ChannelConnectorError as err:
            self.create_issue(
                section='restriction',
                internal_message=str(err),
                channel_message=err.data['message'])

    @api.model
    def create_rplan(self, binding):
        try:
            external_id = self.backend_adapter.create_rplan(binding.name)
        except ChannelConnectorError as err:
            self.create_issue(
                section='restriction',
                internal_message=str(err),
                channel_message=err.data['message'])
        else:
            binding.external_id = external_id
            self.binder.bind(external_id, binding)
