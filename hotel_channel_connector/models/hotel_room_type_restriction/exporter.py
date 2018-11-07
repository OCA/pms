# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from odoo import api, _
_logger = logging.getLogger(__name__)

class HotelRoomTypeRestrictionExporter(Component):
    _name = 'channel.hotel.room.type.restriction.exporter'
    _inherit = 'hotel.channel.exporter'
    _apply_on = ['channel.hotel.room.type.restriction']
    _usage = 'hotel.room.type.restriction.exporter'

    @api.model
    def rename_rplan(self, binding):
        return self.backend_adapter.rename_rplan(
            binding.external_id,
            binding.name)

    @api.model
    def delete_rplan(self, binding):
        return self.backend_adapter.delete_rplan(binding.external_id)

    @api.model
    def create_rplan(self, binding):
        external_id = self.backend_adapter.create_rplan(binding.name)
        binding.external_id = external_id
        self.binder.bind(external_id, binding)
