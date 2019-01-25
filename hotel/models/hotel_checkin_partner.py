# Copyright 2017  Dario Lodeiros
# Copyright 2018  Alexandre Diaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


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
                self.env.context['reservation_id']
            ])
            return folio
        raise ValidationError(_('You only can create checkin from reservations or folios'))

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
            return reservation.partner_id
        return False


    partner_id = fields.Many2one('res.partner', default=_default_partner_id,
                                 required=True)
    reservation_id = fields.Many2one(
        'hotel.reservation', default=_default_reservation_id)
    folio_id = fields.Many2one('hotel.reservation',
        default=_default_folio_id, readonly=True)
    enter_date = fields.Date(default=_default_enter_date, required=True)
    exit_date = fields.Date(default=_default_exit_date, required=True)
    state = fields.Selection([('draft', 'Pending Entry'),
                              ('booking', 'On Board'),
                              ('done', 'Out'),
                              ('cancelled', 'Cancelled')],
                             'State', readonly=True,
                             default=lambda *a: 'draft',
                             track_visibility='onchange')

    # Validation for Departure date is after arrival date.
    @api.multi
    @api.constrains('exit_date','enter_date')
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
    def action_on_board(self):
        for record in self:
            record.state = 'booking'

    @api.multi
    def action_done(self):
        for record in self:
            record.state = 'done'
