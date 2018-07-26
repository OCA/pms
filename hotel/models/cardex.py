# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Dario Lodeiros <>
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import datetime
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, ValidationError
from odoo.addons.hotel import date_utils


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
            date_1 = date_utils.get_datetime(self.enter_date)
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
