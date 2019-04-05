# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Darío Lodeiros <dariodafoz@gmail.com>
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
from openerp import models, api


class HotelReservation(models.Model):
    _inherit = 'hotel.reservation'

    @api.multi
    def print_all_checkins(self):
        checkins = self.env['hotel.checkin.partner']
        for record in self:
            checkins += record.checkin_partner_ids.filtered(
                lambda s: s.state in ('booking', 'done'))
        if checkins:
            return self.env.ref('hotel_l10n_es.action_report_viajero').\
                report_action(checkins)
