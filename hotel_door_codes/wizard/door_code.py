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
import datetime
from datetime import datetime, date, time, timedelta
from odoo import api, fields, models, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class DoorCodeWizard(models.TransientModel):
    _name = 'door_code'

    @api.model
    def _get_default_date_start(self):
        return datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)

    date_start = fields.Date("Inicio periodo",
                             default=_get_default_date_start)
    date_end = fields.Date("Fin del periodo",
                           default=_get_default_date_start)
    door_code = fields.Html(u'Código para la puerta')

    @api.multi
    def doorcode4(self, fecha):
        # Calculate de Door Code... need a date in String format "%Y-%m-%d"
        compan = self.env.user.company_id
        d = datetime.strptime(fecha, DEFAULT_SERVER_DATE_FORMAT)
        dia_semana = datetime.weekday(d)  # Dias a restar y ponerlo en lunes
        d = d - timedelta(days=dia_semana)
        dtxt = d.strftime('%s.%%06d') % d.microsecond
        dtxt = compan.precode + dtxt[4:8] + compan.postcode
        return dtxt

    @api.multi
    def check_code(self):
        entrada = datetime.strptime(
            self.date_start, DEFAULT_SERVER_DATE_FORMAT)
        if datetime.weekday(entrada) == 0:
            entrada = entrada + timedelta(days=1)
        salida = datetime.strptime(
            self.date_end, DEFAULT_SERVER_DATE_FORMAT)
        if datetime.weekday(salida) == 0:
            salida = salida - timedelta(days=1)
        codes = (u'Código de entrada: ' +
                 '<strong><span style="font-size: 2em;">' +
                 self.doorcode4(self.date_start) +
                 '</span></strong>')
        while entrada <= salida:
            if datetime.weekday(entrada) == 0:
                codes += ("<br>" +
                          u'Cambiará el Lunes ' +
                          datetime.strftime(entrada, "%d-%m-%Y") +
                          ' a: <strong><span style="font-size: 2em;">' +
                          self.doorcode4(datetime.strftime(
                              entrada, "%Y-%m-%d")) +
                          '</span></strong>')
            entrada = entrada + timedelta(days=1)

        return self.write({
             'door_code': codes
             })
