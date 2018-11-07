# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import api, models, fields, _
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
_logger = logging.getLogger(__name__)

class NodeRoomType(models.Model):
    _name = 'node.room.type'
    _inherit = 'node.binding'
    _description = 'Node Hotel Room Type'

    name = fields.Char(required=True, translate=True)
    room_ids = fields.Integer()
    # fields.One2many('node.room', 'room_type_id', 'Rooms')
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=0)

    @job(default_channel='root.channel')
    @api.model
    def create_room_type(self):
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='node.room.type.exporter')
            return exporter.create_room_type(self)

    @job(default_channel='root.channel')
    @api.model
    def modify_room_type(self):
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='node.room.type.exporter')
            return exporter.modify_room_type(self)

    @job(default_channel='root.channel')
    @api.model
    def delete_room_type(self):
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='node.room.type.exporter')
            return exporter.delete_room_type(self)

    @job(default_channel='root.channel')
    @api.model
    def fetch_room_types(self, backend):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='node.room.type.importer')
            return importer.fetch_room_types()

class NodeRoomTypeAdapter(Component):
    _name = 'node.room.type.adapter'
    _inherit = 'hotel.node.adapter'
    _apply_on = 'node.room.type'

    def create_room_type(self, name, room_ids):
        return super().create_room_type(name, room_ids)

    def modify_room_type(self, room_type_id, name, room_ids):
        return super().modify_room_type(room_type_id, name, room_ids)

    def delete_room_type(self, room_type_id):
        return super().delete_room_type(room_type_id)

    def fetch_room_types(self):
        return super().fetch_room_types()


class ChannelBindingRoomTypeListener(Component):
    _name = 'node.binding.room.type.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['node.hotel.room.type']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.create_room_type()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record, fields=None):
        record.delete_room_type()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        record.modify_room_type()
