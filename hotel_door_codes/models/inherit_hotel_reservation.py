# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018-2019  Alda Hotels <informatica@aldahotels.com>
#                             Jose Luis Algara <osotranquilo@gmail.com>
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
from openerp import models, fields, api
from datetime import datetime, date, time, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class Inherit_hotel_reservation(models.Model):
    _inherit = 'hotel.reservation'

    @api.multi
    def doorcode4(self, fecha):
        # Calculate de Door Code... need a date in String format "%Y-%m-%d"
        compan = self.env.user.company_id
        if not compan.precode:
            compan.precode = ""
        if not compan.postcode:
            compan.postcode = ""
        d = datetime.strptime(fecha, DEFAULT_SERVER_DATE_FORMAT)
        dia_semana = datetime.weekday(d)  # Dias a restar y ponerlo en lunes
        d = d - timedelta(days=dia_semana)
        dtxt = d.strftime('%s.%%06d') % d.microsecond
        dtxt = compan.precode + dtxt[4:8] + compan.postcode
        return dtxt

    @api.multi
    def _compute_door_codes(self):
        for res in self:
            entrada = datetime.strptime(
                res.checkin[:10], DEFAULT_SERVER_DATE_FORMAT)
            if datetime.weekday(entrada) == 0:
                entrada = entrada + timedelta(days=1)
            salida = datetime.strptime(
                res.checkout[:10], DEFAULT_SERVER_DATE_FORMAT)
            if datetime.weekday(salida) == 0:
                salida = salida - timedelta(days=1)
            codes = (u'Código de entrada: ' +
                     '<strong><span style="font-size: 1.4em;">' +
                     res.doorcode4(datetime.strftime(entrada, "%Y-%m-%d")) +
                     '</span></strong>')
            while entrada <= salida:
                if datetime.weekday(entrada) == 0:
                    codes += ("<br>" +
                              u'Cambiará el Lunes ' +
                              datetime.strftime(entrada, "%d-%m-%Y") +
                              ' a: <strong><span style="font-size: 1.4em;">' +
                              res.doorcode4(datetime.strftime(
                                  entrada, "%Y-%m-%d")) +
                              '</span></strong>')
                entrada = entrada + timedelta(days=1)
            res.door_codes = codes

    door_codes = fields.Html(u'Códigos de entrada',
                             compute='_compute_door_codes')
    box_number = fields.Integer ('Numero de Caja')
    box_code = fields.Char ('Cod. Caja')
