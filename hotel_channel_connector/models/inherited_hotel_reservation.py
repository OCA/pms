# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError
from ..wubook import (
    DEFAULT_WUBOOK_DATE_FORMAT,
    WUBOOK_STATUS_CONFIRMED,
    WUBOOK_STATUS_WAITING,
    WUBOOK_STATUS_REFUSED,
    WUBOOK_STATUS_ACCEPTED,
    WUBOOK_STATUS_CANCELLED,
    WUBOOK_STATUS_CANCELLED_PENALTY,
    WUBOOK_STATUS_BAD)
from odoo.addons.hotel import date_utils
_logger = logging.getLogger(__name__)


class HotelReservation(models.Model):
    _inherit = 'hotel.reservation'

    @api.multi
    def set_access_for_wubook_fields(self):
        for rec in self:
            user = self.env['res.users'].browse(self.env.uid)
            rec.able_to_modify_wubook = user.has_group('base.group_system')

    @api.depends('channel_type','wchannel_id')
    def _get_origin_sale(self):
        for record in self:
            if not record.channel_type:
                record.channel_type = 'door'
            record.origin_sale = (record.channel_type != 'web' or not record.wchannel_id) and \
                                dict(self.fields_get(allfields=['channel_type'])['channel_type']['selection'])[record.channel_type] \
                                or record.wchannel_id.name

    @api.depends('wrid', 'wchannel_id')
    def _is_from_channel(self):
        for record in self:
            record.wis_from_channel = (record.wrid and record.wchannel_id)

    wrid = fields.Char("WuBook Reservation ID", readonly=True)
    wchannel_id = fields.Many2one('wubook.channel.info',
                                  string='WuBook Channel ID',
                                  readonly=True)
    wchannel_reservation_code = fields.Char("WuBook Channel Reservation Code",
                                            readonly=True)
    wis_from_channel = fields.Boolean('WuBooK Is From Channel',
                                      compute=_is_from_channel, store=False,
                                      readonly=True)
    to_read = fields.Boolean('To Read', default=False)
    able_to_modify_wubook = fields.Boolean(compute=set_access_for_wubook_fields, string='Is user able to modify wubook fields?')
    wbook_json = fields.Text(readonly=True)

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
    wcustomer_notes = fields.Text(related='folio_id.wcustomer_notes')
    wmodified = fields.Boolean("WuBook Modified", readonly=True, default=False)
    origin_sale = fields.Char('Origin', compute=_get_origin_sale,
                              store=True)

    @api.model
    def create(self, vals):
        if vals.get('wrid') != None:
            vals.update({'preconfirm': False})
        user = self.env['res.users'].browse(self.env.uid)
        if user.has_group('hotel.group_hotel_call'):
            vals.update({'to_read': True})
        res = super(HotelReservation, self).create(vals)
        if self._context.get('wubook_action', True) and \
                self.env['wubook'].is_valid_account():
            self.env['hotel.virtual.room.availability'].refresh_availability(
                vals['checkin'],
                vals['checkout'],
                vals['product_id'])
            self.env['wubook'].push_availability()
        return res

#     @api.multi
#     def read(self, fields=None, load='_classic_read'):
#         self.to_read = False
#         return super(HotelReservation, self).read(fields=fields, load=load)

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
            self.env['wubook'].push_availability()
        else:
            res = super(HotelReservation, self).write(vals)
        return res

    @api.multi
    def unlink(self):
        vals = []
        for record in self:
            if record.wrid and not record.parent_reservation:
                raise UserError(_("You can't delete wubook reservations"))
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
            self.env['wubook'].push_availability()
        return res

    @api.multi
    def action_cancel(self):
        waction = self._context.get('wubook_action', True)
        if waction:
            for record in self:
                # Can't cancel in Odoo
                if record.wis_from_channel:
                    raise ValidationError(_("Can't cancel reservations \
                                            from OTA's"))
        user = self.env['res.users'].browse(self.env.uid)
        if user.has_group('hotel.group_hotel_call'):
            self.write({'to_read': True, 'to_assign': True})

        res = super(HotelReservation, self).action_cancel()
        if waction and self.env['wubook'].is_valid_account():
            partner_id = self.env['res.users'].browse(self.env.uid).partner_id
            wubook_obj = self.env['wubook']
            for record in self:
                # Only can cancel reservations created directly in wubook
                if record.wrid and record.wrid != '' and \
                        not record.wchannel_id and \
                        record.wstatus in ['1', '2', '4']:
                    wres = wubook_obj.cancel_reservation(
                        record.wrid,
                        'Cancelled by %s' % partner_id.name)
                    if not wres:
                        raise ValidationError(_("Can't cancel reservation \
                                                                on WuBook"))
        return res

    @api.multi
    def confirm(self):
        can_confirm = True
        for record in self:
            if record.wis_from_channel and int(record.wstatus) in WUBOOK_STATUS_BAD:
                can_confirm = False
        if not can_confirm:
            raise ValidationError(_("Can't confirm cancelled reservations"))
        return super(HotelReservation, self).confirm()

    @api.multi
    def generate_copy_values(self, checkin=False, checkout=False):
        self.ensure_one()
        res = super(HotelReservation, self).generate_copy_values(
                                            checkin=checkin, checkout=checkout)
        res.update({
            'wrid': self.wrid,
            'wchannel_id': self.wchannel_id and self.wchannel_id.id or False,
            'wchannel_reservation_code': self.wchannel_reservation_code,
            'wis_from_channel': self.wis_from_channel,
            'to_read': self.to_read,
            'wstatus': self.wstatus,
            'wstatus_reason': self.wstatus_reason,
            'wcustomer_notes': self.wcustomer_notes,
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
        json_reservs, json_tooltips = super(
            HotelReservation,
            self)._hcalendar_reservation_data(reservations)

        reserv_obj = self.env['hotel.reservation']
        for reserv in json_reservs:
            reservation = reserv_obj.browse(reserv[1])
            reserv[13] = reservation.splitted or reservation.wis_from_channel

        return (json_reservs, json_tooltips)

    @api.multi
    def mark_as_readed(self):
        for record in self:
            record.write({'to_read': False, 'to_assign': False})

    @api.onchange('checkin', 'checkout', 'product_id')
    def on_change_checkin_checkout_product_id(self):
        if not self.wis_from_channel:
            return super(HotelReservation, self).\
                                        on_change_checkin_checkout_product_id()
