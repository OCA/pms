# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo import fields, api, _
_logger = logging.getLogger(__name__)


class HotelRoomTypeImporter(Component):
    _name = 'node.room.type.importer'
    _inherit = 'node.importer'
    _apply_on = ['node.room.type']
    _usage = 'node.room.type.importer'

    @api.model
    def fetch_room_types(self):
        results = self.backend_adapter.fetch_room_types()
        room_type_mapper = self.component(usage='import.mapper',
                                          model_name='node.room.type')

        node_room_type_obj = self.env['node.room.type']
        for rec in results:
            map_record = room_type_mapper.map_record(rec)
            room_bind = node_room_type_obj.search([('external_id', '=', rec['id'])],
                                                  limit=1)
            if room_bind:
                room_bind.write(map_record.values())
            else:
                room_bind.create(map_record.values(for_create=True))


class NodeRoomTypeImportMapper(Component):
    _name = 'node.room.type.import.mapper'
    _inherit = 'node.import.mapper'
    _apply_on = 'node.room.type'

    direct = [
        ('id', 'external_id'),
        ('name', 'name'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}
