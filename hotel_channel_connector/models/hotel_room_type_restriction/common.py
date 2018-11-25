# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.addons.queue_job.job import job
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if


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
    @api.multi
    def create_plan(self):
        self.ensure_one()
        if not self.external_id:
            with self.backend_id.work_on(self._name) as work:
                exporter = work.component(usage='hotel.room.type.restriction.exporter')
                exporter.create_rplan(self)

    @job(default_channel='root.channel')
    @api.multi
    def update_plan_name(self):
        self.ensure_one()
        if self.external_id:
            with self.backend_id.work_on(self._name) as work:
                exporter = work.component(usage='hotel.room.type.restriction.exporter')
                exporter.rename_rplan(self)

    @job(default_channel='root.channel')
    @api.multi
    def delete_plan(self):
        self.ensure_one()
        if self.external_id:
            with self.backend_id.work_on(self._name) as work:
                deleter = work.component(usage='hotel.room.type.restriction.deleter')
                deleter.delete_rplan(self)

    @job(default_channel='root.channel')
    @api.model
    def import_restriction_plans(self, backend):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='hotel.room.type.restriction.importer')
            return importer.import_restriction_plans()

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
