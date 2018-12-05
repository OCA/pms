# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.addons.queue_job.job import job
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if


class ChannelHotelReservation(models.Model):
    _name = 'channel.hotel.reservation'
    _inherit = 'channel.binding'
    _inherits = {'hotel.reservation': 'odoo_id'}
    _description = 'Channel Hotel Reservation'

    odoo_id = fields.Many2one(comodel_name='hotel.reservation',
                              string='Reservation',
                              required=True,
                              ondelete='cascade')
    ota_id = fields.Many2one('channel.ota.info',
                             string='Channel OTA ID',
                             readonly=True,
                             old_name='wchannel_id')
    ota_reservation_id = fields.Char("Channel OTA Reservation Code",
                                     readonly=True,
                                     old_name='wchannel_reservation_code')
    channel_raw_data = fields.Text(readonly=True, old_name='wbook_json')

    channel_status = fields.Selection([
        ('0', 'No Channel'),
    ], string='Channel Status', default='0', readonly=True, old_name='wstatus')
    channel_status_reason = fields.Char("Channel Status Reason", readonly=True,
                                        old_name='wstatus_reason')
    channel_modified = fields.Boolean("Channel Modified", readonly=True,
                                      default=False, old_name='wmodified')

    @api.depends('channel_reservation_id', 'ota_id')
    def _is_from_ota(self):
        for record in self:
            record.is_from_ota = (record.external_id and record.ota_id)

    @job(default_channel='root.channel')
    @api.model
    def refresh_availability(self, checkin, checkout, room_id):
        self.env['channel.hotel.room.type.availability'].refresh_availability(
            checkin, checkout, room_id)

    @job(default_channel='root.channel')
    @api.model
    def import_reservation(self, backend, channel_reservation_id):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='hotel.reservation.importer')
            return importer.fetch_booking(channel_reservation_id)

    @job(default_channel='root.channel')
    @api.model
    def import_reservations(self, backend):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='hotel.reservation.importer')
            return importer.fetch_new_bookings()

    @job(default_channel='root.channel')
    @api.multi
    def cancel_reservation(self):
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='hotel.reservation.exporter')
            return exporter.cancel_reservation(self)

    @job(default_channel='root.channel')
    @api.multi
    def mark_booking(self):
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='hotel.reservation.exporter')
            return exporter.mark_booking(self)

    @api.multi
    def write(self, vals):
        if self._context.get('connector_no_export', True) and \
                (vals.get('checkin') or vals.get('checkout') or
                 vals.get('room_id') or vals.get('state')):
            older_vals = []
            new_vals = []
            for record in self:
                older_vals.append({
                    'checkin': record.checkin,
                    'checkout': record.checkout,
                    'room_id': record.room_id,
                })
                new_vals.append({
                    'checkin': vals.get('checkin', record.checkin),
                    'checkout': vals.get('checkout', record.checkout),
                    'room_id': vals.get('room_id', record.room_id),
                })

            res = super(ChannelHotelReservation, self).write(vals)

            channel_room_type_avail_obj = self.env['channel.hotel.room.type.availability']
            for k_i, v_i in enumerate(older_vals):
                channel_room_type_avail_obj.refresh_availability(
                    v_i['checkin'],
                    v_i['checkout'],
                    v_i['room_id'])
                channel_room_type_avail_obj.refresh_availability(
                    new_vals[k_i]['checkin'],
                    new_vals[k_i]['checkout'],
                    new_vals[k_i]['room_id'])
        else:
            res = super(ChannelHotelReservation, self).write(vals)
        return res

    @api.multi
    def unlink(self):
        vals = []
        for record in self:
            if record.is_from_ota and self._context.get('ota_limits', True):
                raise UserError(_("You can't delete OTA's reservations"))
            vals.append({
                'checkin': record.checkin,
                'checkout': record.checkout,
                'room_id': record.room_id.id,
            })
        res = super(ChannelHotelReservation, self).unlink()
        if self._context.get('connector_no_export', True):
            channel_room_type_avail_obj = self.env['channel.hotel.room.type.availability']
            for record in vals:
                channel_room_type_avail_obj.refresh_availability(
                    record['checkin'],
                    record['checkout'],
                    record['room_id'])
        return res

class HotelReservation(models.Model):
    _inherit = 'hotel.reservation'

    @api.multi
    def _set_access_for_channel_fields(self):
        for record in self:
            user = self.env['res.users'].browse(self.env.uid)
            record.able_to_modify_channel = user.has_group('base.group_system')

    # TODO: Dario v2
    # @api.depends('channel_type', 'channel_bind_ids.ota_id')
    # def _get_origin_sale(self):
    #     for record in self:
    #         if not record.channel_type:
    #             record.channel_type = 'door'
    #
    #         if record.channel_type == 'web' and any(record.channel_bind_ids) and \
    #                 record.channel_bind_ids[0].ota_id:
    #             record.origin_sale = record.channel_bind_ids[0].ota_id.name
    #         else:
    #             record.origin_sale = dict(
    #                 self.fields_get(allfields=['channel_type'])['channel_type']['selection']
    #             )[record.channel_type]

    channel_bind_ids = fields.One2many(
        comodel_name='channel.hotel.reservation',
        inverse_name='odoo_id',
        string='Hotel Channel Connector Bindings')
    # TODO: Dario v2
    # origin_sale = fields.Char('Origin', compute=_get_origin_sale,
    #                           store=True)
    is_from_ota = fields.Boolean('Is From OTA',
                                 readonly=True,
                                 old_name='wis_from_channel')
    able_to_modify_channel = fields.Boolean(compute=_set_access_for_channel_fields,
                                            string='Is user able to modify channel fields?',
                                            old_name='able_to_modify_wubook')
    to_read = fields.Boolean('To Read', default=False)
    customer_notes = fields.Text(related='folio_id.customer_notes',
                                 old_name='wcustomer_notes')

    @api.model
    def create(self, vals):
        if vals.get('external_id') is not None:
            vals.update({'preconfirm': False})
        user = self.env['res.users'].browse(self.env.uid)
        if user.has_group('hotel.group_hotel_call'):
            vals.update({'to_read': True})
        return super(HotelReservation, self).create(vals)

    # @api.multi
    # def generate_copy_values(self, checkin=False, checkout=False):
    #     self.ensure_one()
    #     res = super().generate_copy_values(checkin=checkin, checkout=checkout)
    #     res.update({
    #         'channel_reservation_id': self.channel_reservation_id,
    #         'ota_id': self.ota_id and self.ota_id.id or False,
    #         'ota_reservation_code': self.ota_reservation_code,
    #         'is_from_ota': self.is_from_ota,
    #         'to_read': self.to_read,
    #         'wstatus': self.wstatus,
    #         'wstatus_reason': self.wstatus_reason,
    #         'customer_notes': self.customer_notes,
    #     })
    #     return res

    @api.multi
    def action_reservation_checkout(self):
        for record in self:
            if record.state != 'cancelled':
                return super(HotelReservation, record).action_reservation_checkout()

    @api.model
    def _hcalendar_reservation_data(self, reservations):
        json_reservs, json_tooltips = super()._hcalendar_reservation_data(reservations)

        reserv_obj = self.env['hotel.reservation']
        for reserv in json_reservs:
            reservation = reserv_obj.browse(reserv[1])
            reserv[13] = reservation.splitted or reservation.is_from_ota

        return (json_reservs, json_tooltips)

    @api.multi
    def mark_as_readed(self):
        self.write({'to_read': False, 'to_assign': False})

    @api.onchange('checkin', 'checkout')
    def onchange_dates(self):
        if not self.is_from_ota:
            return super().onchange_dates()

class ChannelBindingHotelReservationListener(Component):
    _name = 'channel.binding.hotel.reservation.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['channel.hotel.reservation']


    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.refresh_availability()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        record.push_availability()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record, fields=None):
        record.push_availability()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_cancel(self, record, fields=None):
        record.cancel_reservation()
