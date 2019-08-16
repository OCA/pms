# Copyright 2018-2019 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime, timedelta
from odoo import api, models, fields, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.job import job
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
_logger = logging.getLogger(__name__)


class HotelRoomTypeAvailability(models.Model):
    _name = 'hotel.room.type.availability'
    _inherit = 'mail.thread'

    @api.model
    def _default_max_avail(self):
        room_type_id = self.room_type_id.id or self._context.get('room_type_id')
        channel_room_type = self.env['channel.hotel.room.type'].search([
            ('odoo_id', '=', room_type_id)
        ]) or None
        if channel_room_type:
            return channel_room_type.default_max_avail
        return -1

    @api.model
    def _default_quota(self):
        room_type_id = self.room_type_id.id or self._context.get('room_type_id')
        channel_room_type = self.env['channel.hotel.room.type'].search([
            ('odoo_id', '=', room_type_id)
        ]) or None
        if channel_room_type:
            return channel_room_type.default_quota
        return -1

    room_type_id = fields.Many2one('hotel.room.type', 'Room Type',
                                   required=True, track_visibility='always',
                                   ondelete='cascade')
    channel_bind_ids = fields.One2many(
        comodel_name='channel.hotel.room.type.availability',
        inverse_name='odoo_id',
        string='Hotel Room Type Availability Connector Bindings')

    date = fields.Date('Date', required=True, track_visibility='always')

    quota = fields.Integer("Quota", default=_default_quota,
                           track_visibility='always',
                           help="Quota assigned to the channel.")
    # TODO: WHY max_avail IS READONLY ¿?
    max_avail = fields.Integer("Max. Availability", default=-1, readonly=True,
                               track_visibility='always',
                               help="Maximum simultaneous availability.")

    no_ota = fields.Boolean('No OTA', default=False,
                            track_visibility='onchange',
                            help="Set zero availability to the connected OTAs "
                                 "even when the availability is positive,"
                                 "except to the Online Reception (booking engine)")
    booked = fields.Boolean('Booked', default=False, readonly=True)

    _sql_constraints = [
        ('room_type_registry_unique',
         'unique(room_type_id, date)',
         'Only can exists one availability in the same day for the same room \
          type!')
    ]

    @api.onchange('room_type_id')
    def onchange_room_type_id(self):
        channel_room_type = self.env['channel.hotel.room.type'].search([
            ('odoo_id', '=', self.room_type_id.id)
        ]) or None
        if channel_room_type:
            self.quota = channel_room_type.default_quota
            self.max_avail = channel_room_type.default_max_avail
            self.no_ota = 0

    @api.model
    def create(self, vals):
        vals.update(self._prepare_add_missing_fields(vals))
        return super().create(vals)

    @api.model
    def _prepare_add_missing_fields(self, values):
        """ Deduce missing required fields from the onchange """
        res = {}
        onchange_fields = ['quota', 'max_avail']
        if values.get('room_type_id'):
            record = self.new(values)
            if 'quota' not in values:
                record.quota = record._default_quota()
            if 'max_avail' not in values:
                record.max_avail = record._default_max_avail()
            for field in onchange_fields:
                if field not in values:
                    res[field] = record._fields[field].convert_to_write(record[field], record)
        return res


class ChannelHotelRoomTypeAvailability(models.Model):
    _name = 'channel.hotel.room.type.availability'
    _inherit = 'channel.binding'
    _inherits = {'hotel.room.type.availability': 'odoo_id'}
    _description = 'Channel Availability'

    odoo_id = fields.Many2one(comodel_name='hotel.room.type.availability',
                              required=True,
                              ondelete='cascade')
    channel_avail = fields.Integer("Availability", readonly=True,
                                   track_visibility='always',
                                   help="Availability of the room type for the channel manager."
                                        "This availability is set based on the real availability, "
                                        "the quota, and the max availability.")
    channel_pushed = fields.Boolean("Channel Pushed", readonly=True,
                                    default=False)

    @api.model
    def refresh_availability(self, checkin, checkout, backend_id, room_id=False,
                             room_type_id=False, from_channel=False):
        date_start = fields.Date.from_string(checkin)
        date_end = fields.Date.from_string(checkout)
        if date_start == date_end:
            date_end = date_start + timedelta(days=1)
        # Not count end day of the reservation
        date_diff = (date_end - date_start).days

        channel_room_type_obj = self.env['channel.hotel.room.type']
        channel_room_type_avail_obj = self.env['channel.hotel.room.type.availability']
        if room_type_id:
            room_type_bind = channel_room_type_obj.search([('odoo_id', '=', room_type_id)])
        else:
            domain = [('backend_id', '=', backend_id)]
            if room_id:
                domain.append(('room_ids', 'in', [room_id]))
                # WARNING: more than one binding is currently not expected
            room_type_bind = channel_room_type_obj.search(domain, limit=1)
        if room_type_bind and room_type_bind.external_id:
            _logger.info("==[ODOO->CHANNEL]==== REFRESH AVAILABILITY ==")
            for i in range(0, date_diff):
                ndate_dt = date_start + timedelta(days=i)
                ndate_str = ndate_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                to_eval = []
                # real availability based on rooms
                cavail = len(channel_room_type_obj.odoo_id.check_availability_room_type(
                    ndate_str,
                    ndate_str,
                    room_type_id=room_type_bind.odoo_id.id))
                to_eval.append(cavail)

                room_type_avail_id = channel_room_type_avail_obj.search([
                    ('room_type_id', '=', room_type_bind.odoo_id.id),
                    ('date', '=', ndate_str)], limit=1)

                quota = room_type_avail_id.quota if room_type_avail_id \
                    else room_type_bind.default_quota
                max_avail = room_type_avail_id.max_avail if room_type_avail_id \
                    else room_type_bind.default_max_avail

                if from_channel and quota > 0:
                    quota -= 1
                # We ignore quota and max_avail if its value is -1
                if quota >= 0:
                    to_eval.append(quota)
                if max_avail >= 0:
                    to_eval.append(max_avail)
                # And finally, set the channel avail like the min set value
                avail = max(min(to_eval), 0)

                if room_type_avail_id:
                    # CAVEAT: update channel.hotel.room.type.availability if needed
                    vals_avail = {}
                    if room_type_avail_id.quota != quota:
                        vals_avail.update({'quota': quota})
                        _logger.info(vals_avail)
                    if room_type_avail_id.channel_avail != avail:
                        vals_avail.update({'channel_avail': avail})
                    if self._context.get('update_no_ota', False) or from_channel:
                        vals_avail.update({'channel_pushed': False})
                    if vals_avail:
                        room_type_avail_id.write(vals_avail)

                    # Auto-Fix channel quota and max availability
                    # vals_avail = {}
                    # # TODO: reduce quota by one instead of adjust to current channel availability
                    # if room_type_avail_id.quota > avail:
                    #     vals_avail.update({'quota': avail})
                    #     _logger.info(vals_avail)
                    # if room_type_avail_id.max_avail > avail:
                    #     vals_avail.update({'max_avail': avail})
                    # if vals_avail:
                    #     room_type_avail_id.with_context(
                    #     {'connector_no_export': True}
                    # ).write(vals_avail)
                else:
                    self.env['hotel.room.type.availability'].with_context(
                        {'connector_no_export': True}
                    ).create({
                        'room_type_id': room_type_bind.odoo_id.id,
                        'date': ndate_str,
                        'quota': quota,
                        'channel_bind_ids': [(0, False, {
                            'channel_avail': avail,
                            'channel_pushed': False,
                            'backend_id': backend_id,
                        })]
                    })
            self.push_availability(self.env['channel.backend'].browse(backend_id))

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
    _name = 'binding.hotel.room.type.availability.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['hotel.room.type.availability']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        fields_to_check = ('quota', 'max_avail', 'no_ota')
        fields_checked = [elm for elm in fields_to_check if elm in fields]

        _logger.info("==[on_record_write] :: hotel.room.type.availability==")
        _logger.info(fields)

        if any(fields_checked) and any(record.channel_bind_ids):
            if 'no_ota' in fields_checked:
                self.env.context = dict(self.env.context)
                self.env.context.update({'update_no_ota': True})
            for binding in record.channel_bind_ids:
                binding.refresh_availability(
                    record.date,
                    (datetime.strptime(record.date, DEFAULT_SERVER_DATE_FORMAT).date() +
                     timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT),
                    binding.backend_id.id,
                    room_type_id=record.room_type_id.id)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        if not any(record.channel_bind_ids):
            channel_room_type_avail_obj = self.env[
                'channel.hotel.room.type.availability']
            backends = self.env['channel.backend'].search([])
            for backend in backends:
                # REVIEW :: If you create directly channel_binding, this search
                # return empty
                avail_bind = channel_room_type_avail_obj.search([
                    ('odoo_id', '=', record.id),
                    ('backend_id', '=', backend.id),
                ])
                if not avail_bind:
                    # REVIEW :: WARNING :: This create triggers on_record_write above
                    avail_bind = channel_room_type_avail_obj.create({
                        'odoo_id': record.id,
                        'channel_pushed': False,
                        'backend_id': backend.id,
                    })
                    _logger.info("==[on_record_create] :: hotel.room.type.availability==")
                    _logger.info(avail_bind)
                else:
                    avail_bind.refresh_availability(
                        record.date,
                        (datetime.strptime(record.date, DEFAULT_SERVER_DATE_FORMAT).date() +
                         timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT),
                        backend.id,
                        # room_type_id=record.room_type_id.channel_bind_ids.id,
                        room_type_id=record.room_type_id.id)


class ChannelBindingHotelRoomTypeAvailabilityListener(Component):
    _name = 'channel.binding.hotel.room.type.availability.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['channel.hotel.room.type.availability']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        fields_to_check = ('date', 'channel_avail')
        fields_checked = [elm for elm in fields_to_check if elm in fields]

        _logger.info("==[on_record_write] :: channel.hotel.room.type.availability==")
        _logger.info(fields)

        if any(fields_checked):
            # self.env['channel.backend'].cron_push_changes()
            record.with_context({'connector_no_export': True}).write({'channel_pushed': False})
            # record.push_availability(record.backend_id)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        if any(record.channel_bind_ids):

            _logger.info("==[on_record_create] :: channel.hotel.room.type.availability==")
            _logger.info(fields)

            for binding in record.channel_bind_ids:
                record.refresh_availability(
                    record.date,
                    record.date,
                    binding.backend_id.id,
                    room_type_id=record.room_type_id.id)
                # record.push_availability(record.backend_id)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_fix_channel_availability(self, record, fields=None):
        if any(record.channel_bind_ids):
            for binding in record.channel_bind_ids:
                record.refresh_availability(
                    record.date,
                    record.date,
                    binding.backend_id.id,
                    room_type_id=record.room_type_id.id)
