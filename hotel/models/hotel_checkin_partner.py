# Copyright 2017  Dario Lodeiros
# Copyright 2018  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, ValidationError


class Cardex(models.Model):
    _name = 'cardex'

    # Validation for Departure date is after arrival date.
    @api.constrains('exit_date')
    def validation_dates(self):
        if self.exit_date < self.enter_date:
            raise models.ValidationError(
                _('Departure date (%s) is prior to arrival on %s') %
                (self.exit_date, self.enter_date))

    def default_reservation_id(self):
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].search([
                ('id', '=', self.env.context['reservation_id'])
            ])
            return reservation
        return False

    def default_enter_date(self):
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].search([
                ('id', '=', self.env.context['reservation_id'])
            ])
            return reservation.checkin
        return False

    def default_exit_date(self):
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].search([
                ('id', '=', self.env.context['reservation_id'])
            ])
            return reservation.checkout
        return False

    def default_partner_id(self):
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].search([
                ('id', '=', self.env.context['reservation_id'])
            ])
            return reservation.partner_id
        return False

    @api.onchange('enter_date', 'exit_date')
    def check_change_dates(self):
        if self.exit_date <= self.enter_date:
            date_1 = fields.Date.from_string(self.enter_date)
            date_2 = date_1 + datetime.timedelta(days=1)
            self.update({'exit_date': date_2, })
            raise ValidationError(
                _('Departure date, is prior to arrival. Check it now. %s') %
                (date_2))

    partner_id = fields.Many2one('res.partner', default=default_partner_id,
                                 required=True)
    reservation_id = fields.Many2one(
        'hotel.reservation',
        default=default_reservation_id, readonly=True)
    enter_date = fields.Date(default=default_enter_date, required=True)
    exit_date = fields.Date(default=default_exit_date, required=True)
