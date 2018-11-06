# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import api, models, fields
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
_logger = logging.getLogger(__name__)

class ChannelHotelRoomTypeRestriction(models.Model):
    _name = 'channel.hotel.room.type.restriction'
    _inherit = 'channel.binding'
    _inherits = {'hotel.room.type.restriction': 'odoo_id'}
    _description = 'Channel Hotel Room Type Restriction'

    odoo_id = fields.Many2one(comodel_name='hotel.room.type.restriction',
                              string='Hotel Virtual Room Restriction',
                              required=True,
                              ondelete='cascade')

    @job(default_channel='root.channel')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def create_plan(self):
        self.ensure_one()
        if not self.external_id:
            with self.backend_id.work_on(self._name) as work:
                exporter = work.component(usage='hotel.room.type.restriction.exporter')
                try:
                    exporter.create_rplan(self)
                except ChannelConnectorError as err:
                    self.create_issue(
                        backend=self.backend_id.id,
                        section='restriction',
                        internal_message=_("Can't create restriction plan in WuBook"),
                        channel_message=err.data['message'])

    @job(default_channel='root.channel')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def update_plan_name(self):
        self.ensure_one()
        if self.external_id:
            with self.backend_id.work_on(self._name) as work:
                exporter = work.component(usage='hotel.room.type.restriction.exporter')
                try:
                    exporter.rename_rplan(self)
                except ChannelConnectorError as err:
                    self.create_issue(
                        backend=self.backend_id.id,
                        section='restriction',
                        internal_message=_("Can't modify restriction plan in WuBook"),
                        channel_message=err.data['message'])

    @job(default_channel='root.channel')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def delete_plan(self):
        self.ensure_one()
        if self.external_id:
            with self.backend_id.work_on(self._name) as work:
                exporter = work.component(usage='hotel.room.type.restriction.exporter')
                try:
                    exporter.delete_rplan(self)
                except ChannelConnectorError as err:
                    self.create_issue(
                        backend=self.backend_id.id,
                        section='restriction',
                        internal_message=_("Can't delete restriction plan in WuBook"),
                        channel_message=err.data['message'])

    @job(default_channel='root.channel')
    @api.model
    def import_restriction_plans(self, backend):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='hotel.room.type.restriction.importer')
            try:
                return importer.import_restriction_plans()
            except ChannelConnectorError as err:
                self.create_issue(
                    backend=backend.id,
                    section='restriction',
                    internal_message=_("Can't fetch restriction plans from wubook"),
                    channel_message=err.data['message'])

class HotelRoomTypeRestriction(models.Model):
    _inherit = 'hotel.room.type.restriction'

    channel_bind_ids = fields.One2many(
        comodel_name='channel.hotel.room.type.restriction',
        inverse_name='odoo_id',
        string='Hotel Channel Connector Bindings')

    @api.multi
    @api.depends('name')
    def name_get(self):
        room_type_restriction_obj = self.env['hotel.room.type.restriction']
        org_names = super(HotelRoomTypeRestriction, self).name_get()
        names = []
        for name in org_names:
            restriction_id = room_type_restriction_obj.browse(name[0])
            if any(restriction_id.channel_bind_ids) and \
                    restriction_id.channel_bind_ids[0].external_id:
                names.append((
                    name[0],
                    '%s (%s Backend)' % (name[1],
                                         restriction_id.channel_bind_ids[0].backend_id.name),
                ))
            else:
                names.append((name[0], name[1]))
        return names

class HotelRoomTypeRestrictionAdapter(Component):
    _name = 'channel.hotel.room.type.restriction.adapter'
    _inherit = 'wubook.adapter'
    _apply_on = 'channel.hotel.room.type.restriction'

    def rplan_rplans(self):
        return super(HotelRoomTypeRestrictionAdapter, self).rplan_rplans()

    def create_rplan(self, name):
        return super(HotelRoomTypeRestrictionAdapter, self).create_rplan(name)

    def delete_rplan(self, external_id):
        return super(HotelRoomTypeRestrictionAdapter, self).delete_rplan(external_id)

    def rename_rplan(self, external_id, new_name):
        return super(HotelRoomTypeRestrictionAdapter, self).rename_rplan(external_id, new_name)

class BindingHotelRoomTypeListener(Component):
    _name = 'binding.hotel.room.type.restriction.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['hotel.room.type.restriction']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if any(record.channel_bind_ids) and 'name' in fields:
            record.channel_bind_ids[0].update_plan_name()

class ChannelBindingHotelRoomTypeRestrictionListener(Component):
    _name = 'channel.binding.hotel.room.type.restriction.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['channel.hotel.room.type.restriction']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.create_plan()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record, fields=None):
        record.delete_plan()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if 'name' in fields:
            record.update_plan_name()
