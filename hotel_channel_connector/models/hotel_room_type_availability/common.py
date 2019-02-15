# Copyright 2018-2019 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta
from odoo import api, models, fields, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.job import job
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if


class HotelRoomTypeAvailability(models.Model):
    _name = 'hotel.room.type.availability'
    _inherit = 'mail.thread'

    @api.model
    def _default_max_avail(self):
        if self.room_type_id:
            return self.room_type_id.total_rooms_count
        return -1

    @api.model
    def _default_quota(self):
        room_type_id = self._context.get('room_type_id')
        if room_type_id:
            room_type_id = self.env['hotel.room_type'].browse(room_type_id)
            return room_type_id.default_quota if room_type_id else -1
        return -1

    room_type_id = fields.Many2one('hotel.room.type', 'Room Type',
                                   required=True, track_visibility='always',
                                   ondelete='cascade')
    date = fields.Date('Date', required=True, track_visibility='always')
    max_avail = fields.Integer("Max. Avail", default=-1, readonly=True)
    quota = fields.Integer("Quota", default=_default_quota)
    channel_bind_ids = fields.One2many(
        comodel_name='channel.hotel.room.type.availability',
        inverse_name='odoo_id',
        string='Hotel Room Type Availability Connector Bindings')
    no_ota = fields.Boolean('No OTA', default=False)
    booked = fields.Boolean('Booked', default=False, readonly=True)

    _sql_constraints = [
        ('room_type_registry_unique',
         'unique(room_type_id, date)',
         'Only can exists one availability in the same day for the same room \
          type!')
    ]

    @api.constrains('max_avail', 'quota')
    def _check_max_avail_quota(self):
        for record in self:
            if record.max_avail != -1 and record.max_avail > record.quota:
                raise ValidationError(_("Invalid Max Avail!"))
            if record.quota != -1 and record.quota > record.room_type_id.total_rooms_count:
                raise ValidationError(_("Invalid Quota!"))

    @api.onchange('room_type_id')
    def onchange_room_type_id(self):
        if self.room_type_id:
            self.quota = self.room_type_id.default_quota


class ChannelHotelRoomTypeAvailability(models.Model):
    _name = 'channel.hotel.room.type.availability'
    _inherit = 'channel.binding'
    _inherits = {'hotel.room.type.availability': 'odoo_id'}
    _description = 'Channel Availability'

    # avail = fields.Integer("Avail", default=0, readonly=True)
    odoo_id = fields.Many2one(comodel_name='hotel.room.type.availability',
                              string='Pricelist',
                              required=True,
                              ondelete='cascade')
    channel_pushed = fields.Boolean("Channel Pushed", readonly=True,
                                    default=False)

    @api.constrains('max_avail')
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
                    'internal_message': _(r"The new availability can't be \
                        greater than the max. availability \
                        (%s) [Input: %d\Max: %d]") % (record.room_type_id.name,
                                                      record.avail,
                                                      max_avail),
                    'date_start': record.date,
                    'date_end': record.date,
                })
                # Auto-Fix channel availability
                self._event('on_fix_channel_availability').notify(record)

    @api.model
    def refresh_availability(self, checkin, checkout, backend_id, room_id=False, room_type_id=False):
        date_start = fields.Date.from_string(checkin)
        date_end = fields.Date.from_string(checkout)
        # Not count end day of the reservation
        date_diff = (date_end - date_start).days

        channel_room_type_obj = self.env['channel.hotel.room.type']
        channel_room_type_avail_obj = self.env['hotel.room.type.availability']

        if room_type_id:
            room_type_bind = channel_room_type_obj.browse(room_type_id)
        else:
            domain = [('backend_id', '=', backend_id)]
            if room_id:
                domain.append(('room_ids', 'in', [room_id]))
            room_type_bind = channel_room_type_obj.search(domain, limit=1)
        if room_type_bind and room_type_bind.external_id:
            for i in range(0, date_diff):
                ndate_dt = date_start + timedelta(days=i)
                ndate_str = ndate_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                to_eval = []
                cavail = len(channel_room_type_obj.odoo_id.check_availability_room_type(
                    ndate_str,
                    ndate_str,
                    room_type_id=room_type_bind.odoo.id))
                to_eval.append(cavail)
                to_eval.append(room_type_bind.total_rooms_count)
                room_type_avail_id = channel_room_type_avail_obj.search([
                    ('room_type_id', '=', room_type_bind.odoo.id),
                    ('date', '=', ndate_str)], limit=1)
                if room_type_avail_id:
                    if room_type_avail_id.channel_max_avail >= 0:
                        to_eval.append(
                            room_type_avail_id.channel_max_avail)
                    if room_type_avail_id.quota >= 0:
                        to_eval.append(room_type_avail_id.quota)
                    if room_type_avail_id.max_avail >= 0:
                        to_eval.append(room_type_avail_id.max_avail)
                avail = max(min(to_eval), 0)

                if room_type_avail_id \
                        and avail != room_type_avail_id.avail:
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
            importer = work.component(
                usage='hotel.room.type.availability.importer')
            return importer.import_availability_values(dfrom, dto)

    @job(default_channel='root.channel')
    @api.model
    def push_availability(self, backend):
        with backend.work_on(self._name) as work:
            exporter = work.component(
                usage='hotel.room.type.availability.exporter')
            return exporter.push_availability()


class BindingHotelRoomTypeAvailabilityListener(Component):
    _name = 'binding.hotel.room.type.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['hotel.room.type.availability']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        fields_to_check = ('quota', 'max_avail')
        fields_checked = [elm for elm in fields_to_check if elm in fields]
        if any(fields_checked) and any(record.channel_bind_ids):
            for binding in record.channel_bind_ids:
                binding.refresh_availability(
                    record.checkin,
                    record.checkout,
                    binding.backend_id.id,
                    room_type_id=record.room_type_id.id)

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
                    avail_bind = channel_room_type_avail_obj.create({
                        'odoo_id': record.id,
                        'channel_pushed': False,
                        'backend_id': backend.id,
                    })
                avail_bind.refresh_availability(
                    record.date,
                    record.date,
                    backend.id,
                    room_type_id=record.room_type_id.id)


class ChannelBindingHotelRoomTypeAvailabilityListener(Component):
    _name = 'channel.binding.hotel.room.type.availability.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['channel.hotel.room.type.availability']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        fields_to_check = ('max_avail', 'date')
        fields_checked = [elm for elm in fields_to_check if elm in fields]
        if any(fields_checked):
            record.channel_pushed = False

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_fix_channel_availability(self, record, fields=None):
        if any(record.channel_bind_ids):
            for binding in record.channel_bind_ids:
                record.refresh_availability(
                    record.checkin,
                    record.checkout,
                    binding.backend_id.id,
                    room_type_id=record.room_type_id.id)
