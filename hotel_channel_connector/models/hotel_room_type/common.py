# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
_logger = logging.getLogger(__name__)

class ChannelHotelRoomType(models.Model):
    _name = 'channel.hotel.room.type'
    _inherit = 'channel.binding'
    _inherits = {'hotel.room.type': 'odoo_id'}
    _description = 'Channel Hotel Room'

    odoo_id = fields.Many2one(comodel_name='hotel.room.type',
                              string='Room Type',
                              required=True,
                              ondelete='cascade')
    channel_short_code = fields.Char("Channel Short Code", readonly=True, old_name='wscode')
    ota_capacity = fields.Integer("OTA's Capacity", default=1, old_name='wcapacity')

    @api.onchange('room_ids')
    def _get_capacity(self):
        for rec in self:
            rec.ota_capacity = rec.odoo_id.get_capacity()

    def _check_self_unlink(self):
        if not self.odoo_id:
            self.sudo().unlink()

    @job(default_channel='root.channel')
    @api.model
    def import_rooms(self, backend):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='hotel.room.type.importer')
            try:
                return importer.get_rooms()
            except ChannelConnectorError as err:
                self.create_issue(
                    backend=backend.id,
                    section='room',
                    internal_message=_("Can't import rooms from WuBook"),
                    channel_message=err.data['message'])

    @api.constrains('ota_capacity')
    def _check_ota_capacity(self):
        for record in self:
            if record.ota_capacity < 1:
                raise ValidationError(_("OTA's capacity can't be less than one"))

    @api.multi
    @api.constrains('channel_short_code')
    def _check_channel_short_code(self):
        for record in self:
            if len(record.channel_short_code) > 4:  # Wubook scode max. length
                raise ValidationError(_("Chanel short code can't be longer than 4 characters"))

    @job(default_channel='root.channel')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def create_room(self):
        self.ensure_one()
        if not self.external_id:
            with self.backend_id.work_on(self._name) as work:
                exporter = work.component(usage='hotel.room.type.exporter')
                try:
                    exporter.create_room(self)
                except ChannelConnectorError as err:
                    self.create_issue(
                        backend=self.backend_id.id,
                        section='room',
                        internal_message=_("Can't create room in WuBook"),
                        channel_message=err.data['message'])

    @job(default_channel='root.channel')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def modify_room(self):
        self.ensure_one()
        if self.external_id:
            with self.backend_id.work_on(self._name) as work:
                exporter = work.component(usage='hotel.room.type.exporter')
                try:
                    exporter.modify_room(self)
                except ChannelConnectorError as err:
                    self.create_issue(
                        backend=self.backend_id.id,
                        section='room',
                        internal_message=_("Can't modify rooms in WuBook"),
                        channel_message=err.data['message'])

    @job(default_channel='root.channel')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def delete_room(self):
        self.ensure_one()
        if self.external_id:
            with self.backend_id.work_on(self._name) as work:
                exporter = work.component(usage='hotel.room.type.exporter')
                try:
                    exporter.delete_room(self)
                except ChannelConnectorError as err:
                    self.create_issue(
                        backend=self.backend_id.id,
                        section='room',
                        internal_message=_("Can't delete room in WuBook"),
                        channel_message=err.data['message'])

class HotelRoomType(models.Model):
    _inherit = 'hotel.room.type'

    channel_bind_ids = fields.One2many(
        comodel_name='channel.hotel.room.type',
        inverse_name='odoo_id',
        string='Hotel Channel Connector Bindings')

    capacity = fields.Integer("Capacity", compute="_compute_capacity")

    @api.multi
    def _compute_capacity(self):
        for record in self:
            record.capacity = record.get_capacity()

    @api.onchange('room_ids')
    def _onchange_room_ids(self):
        self._compute_capacity()

    @api.multi
    def get_restrictions(self, date, restriction_plan_id):
        self.ensure_one()
        restriction = self.env['hotel.room.type.restriction.item'].search([
            ('date', '=', date),
            ('room_type_id', '=', self.id),
            ('restriction_id', '=', restriction_plan_id)
        ], limit=1)
        return restriction

    @api.multi
    def create_bindings(self):
        backends = self.env['channel.backend'].search([])
        binding_obj = self.env['channel.hotel.room.type']
        for backend in backends:
            binding = binding_obj.search([
                ('odoo_id', '=', self.id),
                ('backend_id', '=', backend.id)], limit=1)
            if not binding:
                binding_obj.sudo().create({
                    'odoo_id': self.id,
                    'backend_id': backend.id,
                })

class HotelRoomTypeAdapter(Component):
    _name = 'channel.hotel.room.type.adapter'
    _inherit = 'wubook.adapter'
    _apply_on = 'channel.hotel.room.type'

    def fetch_rooms(self):
        return super(HotelRoomTypeAdapter, self).fetch_rooms()

class BindingHotelRoomTypeListener(Component):
    _name = 'binding.hotel.room.type.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['hotel.room.type']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if any(record.channel_bind_ids) and 'name' in fields or 'list_price' in fields or \
                'room_ids' in fields:
            # FIXME: Supossed that only exists one channel connector per record
            record.channel_bind_ids[0].modify_room()

    # @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    # def on_record_create(self, record, fields=None):
    #     record.create_bindings()

class ChannelBindingRoomTypeListener(Component):
    _name = 'channel.binding.room.type.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['channel.hotel.room.type']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.create_room()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record, fields=None):
        record.delete_room()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        record.modify_room()
