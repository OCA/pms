# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta
from odoo import api, models, fields, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo.addons.hotel_channel_connector.components.backend_adapter import (
    DEFAULT_WUBOOK_DATE_FORMAT)

class ChannelHotelRoomTypeAvailability(models.Model):
    _name = 'channel.hotel.room.type.availability'
    _inherit = 'channel.binding'
    _inherits = {'hotel.room.type.availability': 'odoo_id'}
    _description = 'Channel Availability'

    @api.model
    def _default_channel_max_avail(self):
        if self.odoo_id.room_type_id:
            return self.odoo_id.room_type_id.total_rooms_count
        return -1

    odoo_id = fields.Many2one(comodel_name='hotel.room.type.availability',
                              string='Pricelist',
                              required=True,
                              ondelete='cascade')
    channel_max_avail = fields.Integer("Max. Channel Avail",
                                       default=_default_channel_max_avail,
                                       old_name='wmax_avail')
    channel_pushed = fields.Boolean("Channel Pushed", readonly=True, default=False,
                                    old_name='wpushed')

    @api.constrains('channel_max_avail')
    def _check_channel_max_avail(self):
        for record in self:
            if record.channel_max_avail > record.odoo_id.room_type_id.total_rooms_count:
                raise ValidationError(_("max avail for channel can't be high \
                    than total rooms \
                    count: %d") % record.odoo_id.room_type_id.total_rooms_count)

    @job(default_channel='root.channel')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def update_availability(self, backend):
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='hotel.room.type.availability.exporter')
            try:
                return exporter.update_availability(self)
            except ChannelConnectorError as err:
                self.create_issue(
                    backend=backend.id,
                    section='avail',
                    internal_message=_("Can't update availability in WuBook"),
                    channel_message=err.data['message'])

    @job(default_channel='root.channel')
    @api.model
    def import_availability(self, backend):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='hotel.room.type.availability.importer')
            try:
                return importer.get_availability(backend.avail_from, backend.avail_to)
            except ChannelConnectorError as err:
                self.create_issue(
                    backend=backend.id,
                    section='avail',
                    internal_message=_("Can't import availability from WuBook"),
                    channel_message=err.data['message'])

    @job(default_channel='root.channel')
    @api.model
    def push_availability(self, backend):
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='hotel.room.type.availability.exporter')
            try:
                return exporter.push_availability()
            except ChannelConnectorError as err:
                self.create_issue(
                    backend=backend.id,
                    section='avail',
                    internal_message=_("Can't update availability in WuBook"),
                    channel_message=err.data['message'])

class HotelRoomTypeAvailability(models.Model):
    _inherit = 'hotel.room.type.availability'

    channel_bind_ids = fields.One2many(
        comodel_name='channel.hotel.room.type.availability',
        inverse_name='odoo_id',
        string='Hotel Room Type Availability Connector Bindings')

    no_ota = fields.Boolean('No OTA', default=False)
    booked = fields.Boolean('Booked', default=False, readonly=True)

    def _prepare_notif_values(self, record):
        vals = super(HotelRoomTypeAvailability, self)._prepare_notif_values()
        vals.update({
            'no_ota': record.no_ota,
        })
        return vals

    @api.constrains('avail')
    def _check_avail(self):
        room_type_obj = self.env['hotel.room.type']
        issue_obj = self.env['hotel.channel.connector.issue']
        for record in self:
            cavail = len(room_type_obj.check_availability_room_type(
                record.date,
                record.date,
                room_type_id=record.room_type_id.id))
            max_avail = min(cavail, record.room_type_id.total_rooms_count)
            if record.avail > max_avail:
                issue_obj.sudo().create({
                    'section': 'avail',
                    'internal_message': _(r"The new availability can't be greater than \
                        the max. availability \
                        (%s) [Input: %d\Max: %d]") % (record.room_type_id.name,
                                                      record.avail,
                                                      max_avail),
                    'date_start': record.date,
                    'date_end': record.date,
                })
                # Auto-Fix channel availability
                self._event('on_fix_channel_availability').notify(record)
        return super(HotelRoomTypeAvailability, self)._check_avail()

    @api.onchange('room_type_id')
    def onchange_room_type_id(self):
        if self.room_type_id:
            self.channel_max_avail = self.room_type_id.total_rooms_count

    @api.model
    def refresh_availability(self, checkin, checkout, product_id):
        date_start = fields.Date.from_string(checkin)
        date_end = fields.Date.from_string(checkout)
        # Not count end day of the reservation
        date_diff = (date_end - date_start).days

        room_type_obj = self.env['hotel.room.type']
        room_type_avail_obj = self.env['hotel.room.type.availability']

        room_types = room_type_obj.search([
            ('room_ids.product_id', '=', product_id)
        ])
        for room_type in room_types:
            if room_type.channel_room_id:
                for i in range(0, date_diff):
                    ndate_dt = date_start + timedelta(days=i)
                    ndate_str = ndate_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    avail = len(room_type_obj.check_availability_room_type(
                        ndate_str,
                        ndate_str,
                        room_type_id=room_type.id))
                    max_avail = room_type.total_rooms_count
                    room_type_avail_id = room_type_avail_obj.search([
                        ('room_type_id', '=', room_type.id),
                        ('date', '=', ndate_str)], limit=1)
                    if room_type_avail_id and room_type_avail_id.channel_max_avail >= 0:
                        max_avail = room_type_avail_id.channel_max_avail
                    avail = max(
                        min(avail, room_type.total_rooms_count, max_avail), 0)

                    if room_type_avail_id:
                        room_type_avail_id.write({'avail': avail})
                    else:
                        room_type_avail_obj.create({
                            'room_type_id': room_type.id,
                            'date': ndate_str,
                            'avail': avail,
                        })

class HotelRoomTypeAvailabilityAdapter(Component):
    _name = 'channel.hotel.room.type.availability.adapter'
    _inherit = 'wubook.adapter'
    _apply_on = 'channel.hotel.room.type.availability'

    def fetch_rooms_values(self, date_from, date_to, rooms=False):
        return super(HotelRoomTypeAvailabilityAdapter, self).fetch_rooms_values(
            date_from,
            date_to,
            rooms)

    def update_availability(self, rooms_avail):
        return super(HotelRoomTypeAvailabilityAdapter, self).update_availability(
            rooms_avail)

class BindingHotelRoomTypeAvailabilityListener(Component):
    _name = 'binding.hotel.room.type.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['hotel.room.type.availability']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if 'avail' in fields:
            record.channel_bind_ids.write({'channel_pushed': False})

class ChannelBindingHotelRoomTypeAvailabilityListener(Component):
    _name = 'channel.binding.hotel.room.type.availability.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['channel.hotel.room.type.availability']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if 'avail' in fields:
            record.channel_pushed = False

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_fix_channel_availability(self, record, fields=None):
        record.update_availability()
