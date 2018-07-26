# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <dev@redneboa.es>
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
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp import models, api
from odoo.addons.hotel_calendar.controllers.bus import HOTEL_BUS_CHANNEL_ID


class BusHotelCalendar(models.TransientModel):
    _inherit = 'bus.hotel.calendar'

    @api.model
    def _generate_issue_notification(self, ntype, title, issue_id, section,
                                     message):
        user_id = self.env['res.users'].browse(self.env.uid)
        return {
            'type': 'issue',
            'subtype': ntype,
            'title': title,
            'username': user_id.partner_id.name,
            'userid': user_id.id,
            'issue': {
                'issue_id': issue_id,
                'section': section.upper(),
                'message': message,
            },
        }

    @api.model
    def _generate_reservation_notif(self, vals):
        json = super(BusHotelCalendar, self)._generate_reservation_notif(vals)
        json['reservation'].update({
            'wrid': vals['wrid'],
        })
        return json

    @api.model
    def send_issue_notification(self, ntype, title, issue_id, section,
                                message):
        notif = self._generate_issue_notification(ntype, title, issue_id,
                                                  section, message)
        self.env['bus.bus'].sendone(
                    (self._cr.dbname, 'hotel.reservation',
                     HOTEL_BUS_CHANNEL_ID), notif)
