# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.addons.queue_job.job import job, related_action

class ChannelHotelReservation(models.Model):
    _name = 'channel.hotel.reservation'
    _inherit = 'channel.binding'
    _inherits = {'hotel.reservation': 'odoo_id'}
    _description = 'Channel Hotel Reservation'

    @api.depends('channel_reservation_id', 'ota_id')
    def _is_from_ota(self):
        for record in self:
            record.is_from_ota = (record.channel_reservation_id and record.ota_id)

    odoo_id = fields.Many2one(comodel_names='hotel.reservation',
                              string='Reservation',
                              required=True,
                              ondelete='cascade')
    channel_reservation_id = fields.Char("Channel Reservation ID", readonly=True, old_name='wrid')
    ota_id = fields.Many2one('channel.ota.info',
                             string='Channel OTA ID',
                             readonly=True,
                             old_name='wchannel_id')
    ota_reservation_id = fields.Char("Channel OTA Reservation Code",
                                     readonly=True,
                                     old_name='channel_reservation_code')
    is_from_ota = fields.Boolean('Is From OTA',
                                 compute=_is_from_ota, store=False,
                                 readonly=True,
                                 old_name='wis_from_channel')
    to_read = fields.Boolean('To Read', default=False)
    able_to_modify_channel = fields.Boolean(compute=set_access_for_wubook_fields,
                                            string='Is user able to modify wubook fields?',
                                            old_name='able_to_modify_wubook')
    channel_raw_data = fields.Text(readonly=True, old_name='wbook_json')

    wstatus = fields.Selection([
        ('0', 'No WuBook'),
        (str(WUBOOK_STATUS_CONFIRMED), 'Confirmed'),
        (str(WUBOOK_STATUS_WAITING), 'Waiting'),
        (str(WUBOOK_STATUS_REFUSED), 'Refused'),
        (str(WUBOOK_STATUS_ACCEPTED), 'Accepted'),
        (str(WUBOOK_STATUS_CANCELLED), 'Cancelled'),
        (str(WUBOOK_STATUS_CANCELLED_PENALTY), 'Cancelled with penalty')],
                               string='WuBook Status', default='0',
                               readonly=True)
    wstatus_reason = fields.Char("WuBook Status Reason", readonly=True)
    customer_notes = fields.Text(related='folio_id.customer_notes',
                                 old_name='wcustomer_notes')
    wmodified = fields.Boolean("WuBook Modified", readonly=True, default=False)

    @job(default_channel='root.channel')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def push_availability(self):
        self.ensure_one()
        if self._context.get('channel_action', True):
            with self.backend_id.work_on(self._name) as work:
                exporter = work.component(usage='channel.exporter')
                exporter.push_availability()

    @job(default_channel='root.channel')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def cancel_reservation(self):
        self.ensure_one()
        if self._context.get('channel_action', True):
            with self.backend_id.work_on(self._name) as work:
                adapter = work.component(usage='backend.adapter')
                wres = adapter.cancel_reservation(
                    self.channel_reservation_id,
                    _('Cancelled by %s') % partner_id.name)
                if not wres:
                    raise ValidationError(_("Can't cancel reservation on WuBook"))

class HotelReservation(models.Model):
    _inherit = 'hotel.reservation'

    @api.multi
    def set_access_for_wubook_fields(self):
        for rec in self:
            user = self.env['res.users'].browse(self.env.uid)
            rec.able_to_modify_channel = user.has_group('base.group_system')

    @api.depends('channel_type', 'ota_id')
    def _get_origin_sale(self):
        for record in self:
            if not record.channel_type:
                record.channel_type = 'door'
            record.origin_sale = dict(
                self.fields_get(
                    allfields=['channel_type'])['channel_type']['selection'])[record.channel_type] \
                        if record.channel_type != 'web' or not record.ota_id \
                        else record.ota_id.name

    channel_bind_ids = fields.One2many(
        comodel_name='channel.hotel.reservation',
        inverse_name='odoo_id',
        string='Hotel Channel Connector Bindings')
    origin_sale = fields.Char('Origin', compute=_get_origin_sale,
                              store=True)

    @api.model
    def create(self, vals):
        if vals.get('channel_reservation_id') != None:
            vals.update({'preconfirm': False})
        user = self.env['res.users'].browse(self.env.uid)
        if user.has_group('hotel.group_hotel_call'):
            vals.update({'to_read': True})
        res = super(HotelReservation, self).create(vals)
        self.env['hotel.virtual.room.availability'].refresh_availability(
            vals['checkin'],
            vals['checkout'],
            vals['product_id'])
        return res

    @api.multi
    def write(self, vals):
        if self._context.get('wubook_action', True) and \
                self.env['wubook'].is_valid_account() and \
                (vals.get('checkin') or vals.get('checkout') or
                 vals.get('product_id') or vals.get('state')):
            older_vals = []
            new_vals = []
            for record in self:
                prod_id = False
                if record.product_id:
                    prod_id = record.product_id.id
                older_vals.append({
                    'checkin': record.checkin,
                    'checkout': record.checkout,
                    'product_id': prod_id,
                })
                new_vals.append({
                    'checkin': vals.get('checkin', record.checkin),
                    'checkout': vals.get('checkout', record.checkout),
                    'product_id': vals.get('product_id', prod_id),
                })

            res = super(HotelReservation, self).write(vals)

            vroom_avail_obj = self.env['hotel.virtual.room.availability']
            for i in range(0, len(older_vals)):
                vroom_avail_obj.refresh_availability(
                    older_vals[i]['checkin'],
                    older_vals[i]['checkout'],
                    older_vals[i]['product_id'])
                vroom_avail_obj.refresh_availability(
                    new_vals[i]['checkin'],
                    new_vals[i]['checkout'],
                    new_vals[i]['product_id'])
        else:
            res = super(HotelReservation, self).write(vals)
        return res

    @api.multi
    def unlink(self):
        vals = []
        for record in self:
            if record.wrid and not record.parent_reservation:
                raise UserError(_("You can't delete OTA's reservations"))
            vals.append({
                'checkin': record.checkin,
                'checkout': record.checkout,
                'product_id': record.product_id.id,
            })
        res = super(HotelReservation, self).unlink()
        if self._context.get('wubook_action', True) and \
                self.env['wubook'].is_valid_account():
            vroom_avail_obj = self.env['hotel.virtual.room.availability']
            for record in vals:
                vroom_avail_obj.refresh_availability(
                    record['checkin'],
                    record['checkout'],
                    record['product_id'])
        return res

    @api.multi
    def action_cancel(self):
        waction = self._context.get('wubook_action', True)
        if waction:
            for record in self:
                # Can't cancel in Odoo
                if record.is_from_ota:
                    raise ValidationError(_("Can't cancel reservations from OTA's"))
        user = self.env['res.users'].browse(self.env.uid)
        if user.has_group('hotel.group_hotel_call'):
            self.write({'to_read': True, 'to_assign': True})

        res = super(HotelReservation, self).action_cancel()
        if waction and self.env['wubook'].is_valid_account():
            partner_id = self.env['res.users'].browse(self.env.uid).partner_id
            for record in self:
                # Only can cancel reservations created directly in wubook
                if record.channel_reservation_id and not record.ota_id and \
                        record.wstatus in ['1', '2', '4']:
                    self._event('on_record_cancel').notify(record)
        return res

    @api.multi
    def confirm(self):
        can_confirm = True
        for record in self:
            if record.is_from_ota and int(record.wstatus) in WUBOOK_STATUS_BAD:
                can_confirm = False
                break
        if not can_confirm:
            raise ValidationError(_("Can't confirm OTA's cancelled reservations"))
        return super(HotelReservation, self).confirm()

    @api.multi
    def generate_copy_values(self, checkin=False, checkout=False):
        self.ensure_one()
        res = super().generate_copy_values(checkin=checkin, checkout=checkout)
        res.update({
            'channel_reservation_id': self.channel_reservation_id,
            'ota_id': self.ota_id and self.ota_id.id or False,
            'ota_reservation_code': self.ota_reservation_code,
            'is_from_ota': self.is_from_ota,
            'to_read': self.to_read,
            'wstatus': self.wstatus,
            'wstatus_reason': self.wstatus_reason,
            'customer_notes': self.customer_notes,
        })
        return res

    @api.multi
    def action_reservation_checkout(self):
        for record in self:
            if record.state == 'cancelled':
                return
            else:
                return super(HotelReservation, record).\
                                                action_reservation_checkout()

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

    @api.onchange('checkin', 'checkout', 'product_id')
    def on_change_checkin_checkout_product_id(self):
        if not self.is_from_ota:
            return super().on_change_checkin_checkout_product_id()

class ChannelBindingProductListener(Component):
    _name = 'channel.binding.hotel.reservation.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['channel.hotel.reservation']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        record.with_delay(priority=20).push_availability()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record, fields=None):
        record.with_delay(priority=20).push_availability()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_cancel(self, record, fields=None):
        record.with_delay(priority=20).cancel_reservation()
