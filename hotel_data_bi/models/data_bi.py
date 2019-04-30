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
            archivo == 0 'ALL'
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

        if not isinstance(archivo, int):
            archivo = 0
            dic_param = []
            dic_param.append({'Archivo': archivo,
                              'Fechafoto': fechafoto.strftime('%Y-%m-%d')})
        compan = self.env.user.company_id

        dic_export = []  # Diccionario con todo lo necesario para exportar.
        if (archivo == 0) or (archivo == 1):
            dic_tarifa = self.data_bi_tarifa(compan.id_hotel)
            dic_export.append({'Tarifa': dic_tarifa})
        if (archivo == 0) or (archivo == 2):
            dic_canal = self.data_bi_canal(compan.id_hotel)
            dic_export.append({'Canal': dic_canal})
        if (archivo == 0) or (archivo == 3):
            dic_hotel = self.data_bi_hotel(compan)
            dic_export.append({'Hotel': dic_hotel})
        if (archivo == 0) or (archivo == 4):
            dic_pais = self.data_bi_pais(compan.id_hotel)
            dic_export.append({'Pais': dic_pais})
        if (archivo == 0) or (archivo == 5):
            dic_regimen = self.data_bi_regimen(compan.id_hotel)
            dic_export.append({'Regimen': dic_regimen})
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
        if (archivo == 0) or (archivo == 14):
            dic_estados = self.data_bi_estados(compan.id_hotel)
            dic_export.append({'Estado Reservas': dic_estados})

        # Debug Stop -------------------
        import wdb; wdb.set_trace()
        # Debug Stop -------------------
        dictionaryToJson = json.dumps(dic_export)
        _logger.warning("End Export Data_Bi Module to Json")

        return dictionaryToJson

    @api.model
    def data_bi_tarifa(self, compan):
        dic_tarifa = []  # Diccionario con las tarifas
        tarifas = self.env['product.pricelist'].search_read([], ['name'])
        for tarifa in tarifas:
            dic_tarifa.append({'ID_Hotel': compan,
                               'ID_Tarifa': tarifa['id'],
                               'Descripcion': tarifa['name']})
        return dic_tarifa

    @api.model
    def data_bi_canal(self, compan):
        dic_canal = []  # Diccionario con los Canales
        canal_array = ['Directo', 'OTA', 'Call-Center', 'Agencia',
                       'Touroperador']
        for i in range(0, len(canal_array)):
            dic_canal.append({'ID_Hotel': compan,
                              'ID_Canal': i,
                              'Descripcion': canal_array[i]})
        return dic_canal

    @api.model
    def data_bi_hotel(self, compan):
        dic_hotel = []  # Diccionario con el/los nombre de los hoteles
        dic_hotel.append({'ID_Hotel': compan.id_hotel,
                          'Descripcion': compan.property_name})
        return dic_hotel

    @api.model
    def data_bi_pais(self, compan):
        dic_pais = []
        # Diccionario con los nombre de los Paises usando los del INE
        paises = self.env['code.ine'].search_read([], ['code', 'name'])
        for pais in paises:
            dic_pais.append({'ID_Hotel': compan,
                             'ID_Pais': pais['code'],
                             'Descripcion': pais['name']})
        return dic_pais

    @api.model
    def data_bi_regimen(self, compan):
        dic_regimen = []  # Diccionario con los Board Services
        board_services = self.env['hotel.board.service'].search_read([])
        dic_regimen.append({'ID_Hotel': compan,
                            'ID_Regimen': 0,
                            'Descripcion': 'Sin régimen'})
        for board_service in board_services:
            dic_regimen.append({'ID_Hotel': compan,
                                'ID_Regimen': board_service['id'],
                                'Descripcion': board_service['name']})
        return dic_regimen

    @api.model
    def data_bi_estados(self, compan):
        dic_estados = []  # Diccionario con los Estados Reserva
        estado_array_txt = ['Borrador', 'Confirmada', 'Hospedandose',
                            'Checkout', 'Cancelada']
        estado_array = ['draft', 'confirm', 'booking', 'done', 'cancelled']
        for i in range(0, len(estado_array)):
            dic_estados.append({'ID_Hotel': compan,
                                'ID_EstadoReserva': i,
                                'Descripcion': estado_array_txt[i]})
        return dic_estados
