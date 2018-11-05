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
                backend=self.backend_adapter.id,
                section='restriction',
                internal_message=_("Can't modify restriction plan in WuBook"),
                channel_message=err.data['message'])

    @api.model
    def delete_rplan(self, binding):
        try:
            return self.backend_adapter.delete_rplan(binding.external_id)
        except ChannelConnectorError as err:
            self.create_issue(
                backend=self.backend_adapter.id,
                section='restriction',
                internal_message=_("Can't delete restriction plan in WuBook"),
                channel_message=err.data['message'])

    @api.model
    def create_rplan(self, binding):
        try:
            external_id = self.backend_adapter.create_rplan(binding.name)
            binding.external_id = external_id
        except ChannelConnectorError as err:
            self.create_issue(
                backend=self.backend_adapter.id,
                section='restriction',
                internal_message=_("Can't create restriction plan in WuBook"),
                channel_message=err.data['message'])
        else:
            self.binder.bind(external_id, binding)
