# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta
from odoo import api, models, fields, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.job import job
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if


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

    @api.model
    def refresh_availability(self, checkin, checkout, room_id):
        date_start = fields.Date.from_string(checkin)
        date_end = fields.Date.from_string(checkout)
        # Not count end day of the reservation
        date_diff = (date_end - date_start).days

        channel_room_type_obj = self.env['channel.hotel.room.type']
        channel_room_type_avail_obj = self.env['hotel.room.type.availability']

        room_type_binds = channel_room_type_obj.search([
            ('backend_id', '=', self.backend_id.id),
            ('room_ids', '=', room_id),
        ])
        for room_type_bind in room_type_binds:
            if room_type_bind.external_id:
                for i in range(0, date_diff):
                    ndate_dt = date_start + timedelta(days=i)
                    ndate_str = ndate_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    avail = len(channel_room_type_obj.odoo_id.check_availability_room_type(
                        ndate_str,
                        ndate_str,
                        room_type_id=room_type_bind.odoo.id))
                    max_avail = room_type_bind.total_rooms_count
                    room_type_avail_id = channel_room_type_avail_obj.search([
                        ('room_type_id', '=', room_type_bind.odoo.id),
                        ('date', '=', ndate_str)], limit=1)
                    if room_type_avail_id and room_type_avail_id.channel_max_avail >= 0:
                        max_avail = room_type_avail_id.channel_max_avail
                    avail = max(
                        min(avail, room_type_bind.total_rooms_count, max_avail), 0)

                    if room_type_avail_id:
                        room_type_avail_id.write({'avail': avail})
                    else:
                        channel_room_type_avail_obj.create({
                            'room_type_id': room_type_bind.odoo.id,
                            'date': ndate_str,
                            'avail': avail,
                        })

    @job(default_channel='root.channel')
    @api.model
    def import_availability(self, backend, dfrom, dto):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='hotel.room.type.availability.importer')
            return importer.import_availability_values(dfrom, dto)

    @job(default_channel='root.channel')
    @api.model
    def push_availability(self, backend):
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='hotel.room.type.availability.exporter')
            return exporter.push_availability()

class HotelRoomTypeAvailability(models.Model):
    _inherit = 'hotel.room.type.availability'

    channel_bind_ids = fields.One2many(
        comodel_name='channel.hotel.room.type.availability',
        inverse_name='odoo_id',
        string='Hotel Room Type Availability Connector Bindings')

    no_ota = fields.Boolean('No OTA', default=False)
    booked = fields.Boolean('Booked', default=False, readonly=True)

    def _prepare_notif_values(self, record):
        vals = super(HotelRoomTypeAvailability, self)._prepare_notif_values(record)
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

class BindingHotelRoomTypeAvailabilityListener(Component):
    _name = 'binding.hotel.room.type.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['hotel.room.type.availability']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if 'avail' in fields:
            record.channel_bind_ids.write({'channel_pushed': False})

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        if not any(record.channel_bind_ids):
            channel_room_type_avail_obj = self.env[
                'channel.hotel.room.type.availability']
            backends = self.env['channel.backend'].search([])
            for backend in backends:
                avail_bind = channel_room_type_avail_obj.search([
                    ('odoo_id', '=', record.id),
                    ('backend_id', '=', backend.id),
                ])
                if not avail_bind:
                    channel_room_type_avail_obj.create({
                        'odoo_id': record.id,
                        'channel_pushed': False,
                        'backend_id': backend.id,
                    })

class ChannelBindingHotelRoomTypeAvailabilityListener(Component):
    _name = 'channel.binding.hotel.room.type.availability.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['channel.hotel.room.type.availability']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        fields_to_check = ('avail', 'date')
        fields_checked = [elm for elm in fields_to_check if elm in fields]
        if any(fields_checked):
            record.channel_pushed = False

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_fix_channel_availability(self, record, fields=None):
        record.update_availability()
