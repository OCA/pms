# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2018-2019 Jose Luis Algara Toledo <osotranquilo@gmail.com>
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
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class DoorCodeWizard(models.TransientModel):
    _name = 'door_code'
    _description = 'Door Code Generator'

    # Default methods
    
    def _get_default_date_start(self):
        return datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)

    # Fields declaration
    date_start = fields.Date(
        "Start of the period",
        default=_get_default_date_start)
    date_end = fields.Date(
        "End of period",
        default=_get_default_date_start)
    door_code = fields.Html("Door code")

    
    def check_code(self):
        reservation = self.env['hotel.reservation']

        entrada = datetime.strptime(
            self.date_start, DEFAULT_SERVER_DATE_FORMAT)
        if datetime.weekday(entrada) == 0:
            entrada = entrada + timedelta(days=1)
        salida = datetime.strptime(
            self.date_end, DEFAULT_SERVER_DATE_FORMAT)
        if datetime.weekday(salida) == 0:
            salida = salida - timedelta(days=1)
        codes = (_('Entry Code: ') +
                 '<strong><span style="font-size: 2em;">' +
                 reservation.doorcode4(self.date_start) +
                 '</span></strong>')
        while entrada <= salida:
            if datetime.weekday(entrada) == 0:
                codes += ("<br>" +
                          _('It will change on ') +
                          datetime.strftime(entrada, "%d-%m-%Y") +
                          _(' to:') +
                          '<strong><span style="font-size: 2em;">' +
                          reservation.doorcode4(datetime.strftime(
                              entrada, "%Y-%m-%d")) +
                          '</span></strong>')
            entrada = entrada + timedelta(days=1)

        return self.write({
             'door_code': codes,
             'name': 'Ya te digo',
             'clear_breadcrumb': True,
             'target': 'current',
             })
