# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from odoo import api, _
_logger = logging.getLogger(__name__)

class NodeRoomTypeExporter(Component):
    _name = 'node.room.type.exporter'
    _inherit = 'node.exporter'
    _apply_on = ['node.room.type']
    _usage = 'node.room.type.exporter'

    @api.model
    def modify_room(self, binding):
        return self.backend_adapter.modify_room(
            binding.room_type_id,
            binding.name,
            binding.room_ids
        )

    @api.model
    def delete_room(self, binding):
        return self.backend_adapter.delete_room(binding.room_type_id)

    @api.model
    def create_room(self, binding):
        external_id = self.backend_adapter.create_room(
            binding.name,
            binding.room_ids
        )
        self.binder.bind(external_id, binding)
