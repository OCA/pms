# Copyright 2017  Dario Lodeiros
# Copyright 2018  Alexandre Diaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT)


class HotelCheckinPartner(models.Model):
    _name = 'hotel.checkin.partner'

    def _default_reservation_id(self):
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].browse([
                self.env.context['reservation_id']
            ])
            return reservation
        return False

    def _default_folio_id(self):
        if 'folio_id' in self.env.context:
            folio = self.env['hotel.folio'].browse([
                self.env.context['folio_id']
            ])
            return folio
        if 'reservation_id' in self.env.context:
            folio = self.env['hotel.reservation'].browse([
                self.env.context['reservation_id']
            ]).folio_id
            return folio
        return False

    def _default_enter_date(self):
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].browse([
                self.env.context['reservation_id']
            ])
            return reservation.checkin
        return False

    def _default_exit_date(self):
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].browse([
                self.env.context['reservation_id']
            ])
            return reservation.checkout
        return False

    def _default_partner_id(self):
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].browse([
                self.env.context['reservation_id']
            ])
            if reservation.partner_id.id not in reservation.mapped(
                    'checkin_partner_ids.partner_id.id'):
                return reservation.partner_id
        return False

    def _default_to_enter(self):
        tz_hotel = self.env['ir.default'].sudo().get(
            'res.config.settings', 'tz_hotel')
        today = fields.Date.context_today(self.with_context(tz=tz_hotel))
        today_str = fields.Date.from_string(today).strftime(
            DEFAULT_SERVER_DATE_FORMAT)
        if self._default_enter_date() == today_str:
            return True
        return False

    partner_id = fields.Many2one('res.partner', default=_default_partner_id,
                                 required=True)
    email = fields.Char('E-mail', related='partner_id.email')
    mobile = fields.Char('Mobile', related='partner_id.mobile')
    reservation_id = fields.Many2one(
        'hotel.reservation', default=_default_reservation_id)
    folio_id = fields.Many2one('hotel.folio',
                               default=_default_folio_id,
                               readonly=True, required=True)
    enter_date = fields.Date(default=_default_enter_date, required=True)
    exit_date = fields.Date(default=_default_exit_date, required=True)
    auto_booking = fields.Boolean('Get in Now', default=_default_to_enter)
    state = fields.Selection([('draft', 'Pending Entry'),
                              ('booking', 'On Board'),
                              ('done', 'Out'),
                              ('cancelled', 'Cancelled')],
                             'State', readonly=True,
                             default=lambda *a: 'draft',
                             track_visibility='onchange')

    @api.model
    def create(self, vals):
        record = super(HotelCheckinPartner, self).create(vals)
        if vals.get('auto_booking', False):
            record.action_on_board()
        return record

    # Validation for Departure date is after arrival date.
    @api.multi
    @api.constrains('exit_date', 'enter_date')
    def _check_exit_date(self):
        for record in self:
            date_in = fields.Date.from_string(record.enter_date)
            date_out = fields.Date.from_string(record.exit_date)
            if date_out < date_in:
                raise models.ValidationError(
                    _('Departure date (%s) is prior to arrival on %s') %
                    (date_out, date_in))

    @api.onchange('enter_date', 'exit_date')
    def _onchange_enter_date(self):
        date_in = fields.Date.from_string(self.enter_date)
        date_out = fields.Date.from_string(self.exit_date)
        if date_out <= date_in:
            date_out = date_in + datetime.timedelta(days=1)
            self.update({'exit_date': date_out})
            raise ValidationError(
                _('Departure date, is prior to arrival. Check it now. %s') %
                date_out)

    @api.multi
    @api.onchange('partner_id')
    def _check_partner_id(self):
        for record in self:
            checkins = self.env['hotel.checkin.partner'].search([
                            ('id', '!=', record.id),
                            ('reservation_id', '=', record.reservation_id.id)
                        ])
            if record.partner_id.id in checkins.mapped('partner_id.id'):
                raise models.ValidationError(
                    _('This guest is already registered in the room'))

    @api.multi
    @api.constrains('partner_id')
    def _check_partner_id(self):
        for record in self:
            checkins = self.env['hotel.checkin.partner'].search([
                            ('id', '!=', record.id),
                            ('reservation_id', '=', record.reservation_id.id)
                        ])
            if record.partner_id.id in checkins.mapped('partner_id.id'):
                raise models.ValidationError(
                    _('This guest is already registered in the room'))

    @api.multi
    def action_on_board(self):
        for record in self:
            record.state = 'booking'
            if record.reservation_id.state == 'confirm':
                record.reservation_id.state = 'booking'

    @api.multi
    def action_done(self):
        for record in self:
            record.state = 'done'
