# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018 -2019 Alda Hotels <informatica@aldahotels.com>
#                       Jose Luis Algara <osotranquilo@gmail.com>
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
from openerp import models, fields, api, _
from datetime import date, datetime, timedelta
import json
import logging
_logger = logging.getLogger(__name__)


def inv_percent(amount, percent):
    """Return the amount to which a percentage was applied."""
    return round(amount*(100/float(100-percent)) - amount, 2)


class Data_Bi(models.Model):
    """Management and export data for MopSolution MyDataBI."""

    _name = 'data_bi'

    @api.model
    def export_data_bi(self,
                       archivo=False,
                       fechafoto=date.today().strftime('%Y-%m-%d')):
        u"""Prepare a Json Objet to export data for MyDataBI.

        Generate a dicctionary to by send in JSON
        archivo = response file type
            archivo == 1 'Tarifa'
            archivo == 2 'Canal'
            archivo == 3 'Hotel'
            archivo == 4 'Pais'
            archivo == 5 'Regimen'
            archivo == 6 'Reservas'
            archivo == 7 'Capacidad'
            archivo == 8 'Tipo Habitación'
            archivo == 9 'Budget'
            archivo == 10 'Bloqueos'
            archivo == 11 'Motivo Bloqueo'
            archivo == 12 'Segmentos'
            archivo == 13 'Clientes'
            archivo == 14 'Estado Reservas'
        fechafoto = start date to take data
        """

        if type(fechafoto) is dict:
            fechafoto = date.today()
        else:
            fechafoto = datetime.strptime(fechafoto, '%Y-%m-%d').date()

        _logger.warning("Init Export Data_Bi Module")

        dic_export = []  # Diccionario con todo lo necesario para exportar.
        # if (archivo == 0) or (archivo == 1):
        #     dic_export.append({'Tarifa': dic_tarifa})
        # if (archivo == 0) or (archivo == 2):
        #     dic_export.append({'Canal': dic_canal})
        # if (archivo == 0) or (archivo == 3):
        #     dic_export.append({'Hotel': dic_hotel})
        # if (archivo == 0) or (archivo == 4):
        #     dic_export.append({'Pais': dic_pais})
        # if (archivo == 0) or (archivo == 5):
        #     dic_export.append({'Regimen': dic_regimen})
        # if (archivo == 0) or (archivo == 6):
        #     dic_export.append({'Reservas': dic_reservas})
        # if (archivo == 0) or (archivo == 7):
        #     dic_export.append({'Capacidad': dic_capacidad})
        # if (archivo == 0) or (archivo == 8):
        #     dic_export.append({'Tipo Habitación': dic_tipo_habitacion})
        # if (archivo == 0) or (archivo == 9):
        #     dic_export.append({'Budget': dic_budget})
        # if (archivo == 0) or (archivo == 10):
        #     dic_export.append({'Bloqueos': dic_bloqueos})
        # if (archivo == 0) or (archivo == 11):
        #     dic_export.append({'Motivo Bloqueo': dic_moti_bloq})
        # if (archivo == 0) or (archivo == 12):
        #     dic_export.append({'Segmentos': dic_segmentos})
        # if (archivo == 0) or (archivo == 13):
        #     dic_export.append({'Clientes': dic_clientes})
        # if (archivo == 0) or (archivo == 14):
        #     dic_export.append({'Estado Reservas': dic_estados})

        dictionaryToJson = json.dumps(dic_export)
        _logger.warning("End Export Data_Bi Module to Json")

        # Debug Stop -------------------
        # import wdb; wdb.set_trace()
        # Debug Stop -------------------
        return dictionaryToJson
