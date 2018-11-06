# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError

class ChannelHotelRoomTypeRestrictionItem(models.Model):
    _name = 'channel.hotel.room.type.restriction.item'
    _inherit = 'channel.binding'
    _inherits = {'hotel.room.type.restriction.item': 'odoo_id'}
    _description = 'Channel Hotel Room Type Restriction Item'

    odoo_id = fields.Many2one(comodel_name='hotel.room.type.restriction.item',
                              string='Hotel Virtual Room Restriction',
                              required=True,
                              ondelete='cascade')
    channel_pushed = fields.Boolean("Channel Pushed", readonly=True, default=False,
                                    old_name='wpushed')

    @job(default_channel='root.channel')
    @api.model
    def import_restriction_values(self, backend):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='hotel.room.type.restriction.item.importer')
            try:
                return importer.import_restriction_values(
                    backend.restriction_from,
                    backend.restriction_to,
                    channel_restr_id=backend.restriction_id)
            except ChannelConnectorError as err:
                self.create_issue(
                    backend=backend.id,
                    section='restriction',
                    internal_message=_("Can't fetch plan restrictions from wubook"),
                    channel_message=err.data['message'],
                    channel_object_id=backend.restriction_id,
                    dfrom=backend.restriction_from, dto=backend.restriction_to)

    @job(default_channel='root.channel')
    @api.model
    def push_restriction(self, backend):
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='hotel.room.type.restriction.item.exporter')
            try:
                return exporter.push_restriction()
            except ChannelConnectorError as err:
                self.create_issue(
                    backend=backend.id,
                    section='restriction',
                    internal_message=_("Can't update restrictions in WuBook"),
                    channel_message=err.data['message'])

class HotelRoomTypeRestrictionItem(models.Model):
    _inherit = 'hotel.room.type.restriction.item'

    channel_bind_ids = fields.One2many(
        comodel_name='channel.hotel.room.type.restriction.item',
        inverse_name='odoo_id',
        string='Hotel Channel Connector Bindings')

class HotelRoomTypeRestrictionItemAdapter(Component):
    _name = 'channel.hotel.room.type.restriction.item.adapter'
    _inherit = 'wubook.adapter'
    _apply_on = 'channel.hotel.room.type.restriction.item'

    def wired_rplan_get_rplan_values(self, date_from, date_to, channel_restriction_plan_id):
        return super(HotelRoomTypeRestrictionItemAdapter, self).wired_rplan_get_rplan_values(
            date_from,
            date_to,
            channel_restriction_plan_id)

class BindingHotelRoomTypeRestrictionItemListener(Component):
    _name = 'binding.hotel.room.type.restriction.item.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['hotel.room.type.restriction.item']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        fields_to_check = ('min_stay', 'min_stay_arrival', 'max_stay', 'max_stay_arrival',
                           'max_stay_arrival', 'closed', 'closed_departure', 'closed_arrival',
                           'date')
        fields_checked = [elm for elm in fields_to_check if elm in fields]
        if any(fields_checked):
            record.channel_bind_ids.write({'channel_pushed': False})

class ChannelBindingHotelRoomTypeRestrictionItemListener(Component):
    _name = 'channel.binding.hotel.room.type.restriction.item.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['channel.hotel.room.type.restriction.item']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        fields_to_check = ('min_stay', 'min_stay_arrival', 'max_stay', 'max_stay_arrival',
                           'max_stay_arrival', 'closed', 'closed_departure', 'closed_arrival',
                           'date')
        fields_checked = [elm for elm in fields_to_check if elm in fields]
        if any(fields_checked):
            record.channel_pushed = False
