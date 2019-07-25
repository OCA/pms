
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
from openerp import models, api, _
from datetime import date, datetime, timedelta
import json
import logging
_logger = logging.getLogger(__name__)


def inv_percent_inc(amount, percent):
    """Return the amount to which a percentage was increment applied."""
    return (amount - (amount*(100-percent))/100)


def inv_percent(amount, percent):
    """Return the amount to which a percentage was applied."""
    return amount/((100-percent)/100)


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
        limit_ago = (fechafoto - timedelta(
            days=self.env.user.company_id.data_bi_days)).strftime('%Y-%m-%d')

        dic_export = []  # Diccionario con todo lo necesario para exportar.
        if (archivo == 0) or (archivo == 7) or (archivo == 8):
            room_types = self.env['hotel.room.type'].search([])
        if (archivo == 0) or (archivo == 10) or (archivo == 6):
            line_res = self.env['hotel.reservation.line'].search(
                                    [('date', '>=', limit_ago)], order="id")
        estado_array = ['draft', 'confirm', 'booking', 'done', 'cancelled']

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
        if (archivo == 0) or (archivo == 7):
            dic_capacidad = self.data_bi_capacidad(compan.id_hotel, room_types)
            dic_export.append({'Capacidad': dic_capacidad})
        if (archivo == 0) or (archivo == 8):
            dic_tipo_habitacion = self.data_bi_habitacione(compan.id_hotel,
                                                           room_types)
            dic_export.append({'Tipo Habitación': dic_tipo_habitacion})
        if (archivo == 0) or (archivo == 9):
            dic_budget = self.data_bi_budget(compan.id_hotel)
            dic_export.append({'Budget': dic_budget})
        if (archivo == 0) or (archivo == 10):
            dic_bloqueos = self.data_bi_bloqueos(compan.id_hotel, line_res)
            dic_export.append({'Bloqueos': dic_bloqueos})
        if (archivo == 0) or (archivo == 11):
            dic_moti_bloq = self.data_bi_moti_bloq(compan.id_hotel)
            dic_export.append({'Motivo Bloqueo': dic_moti_bloq})
        if (archivo == 0) or (archivo == 12):
            dic_segmentos = self.data_bi_segment(compan.id_hotel)
            dic_export.append({'Segmentos': dic_segmentos})
        if (archivo == 0) or (archivo == 13) or (archivo == 6):
            dic_clientes = self.data_bi_client(compan.id_hotel)
            if (archivo == 0) or (archivo == 13):
                dic_export.append({'Clientes': dic_clientes})
        if (archivo == 0) or (archivo == 14):
            dic_estados = self.data_bi_estados(compan.id_hotel, estado_array)
            dic_export.append({'Estado Reservas': dic_estados})
        if (archivo == 0) or (archivo == 6):
            dic_reservas = self.data_bi_reservas(compan.id_hotel,
                                                 line_res,
                                                 estado_array,
                                                 dic_clientes)
            dic_export.append({'Reservas': dic_reservas})

        dictionaryToJson = json.dumps(dic_export)
        _logger.warning("End Export Data_Bi Module to Json")
        # Debug Stop -------------------
        # import wdb; wdb.set_trace()
        # Debug Stop -------------------

        return dictionaryToJson

    @api.model
    def data_bi_tarifa(self, compan):
        dic_tarifa = []  # Diccionario con las tarifas
        tarifas = self.env['product.pricelist'].search_read([], ['name'])
        _logger.info("DataBi: Calculating %s fees", str(len(tarifas)))
        for tarifa in tarifas:
            dic_tarifa.append({'ID_Hotel': compan,
                               'ID_Tarifa': tarifa['id'],
                               'Descripcion': tarifa['name']})
        return dic_tarifa

    @api.model
    def data_bi_canal(self, compan):
        _logger.info("DataBi: Calculating all channels")
        dic_canal = []  # Diccionario con los Canales
        canal_array = ['Puerta', 'Mail', 'Telefono', 'Call Center', 'Web',
                       'Agencia', 'Touroperador', 'Virtual Door']
        for i in range(0, len(canal_array)):
            dic_canal.append({'ID_Hotel': compan,
                              'ID_Canal': i,
                              'Descripcion': canal_array[i]})
        return dic_canal

    @api.model
    def data_bi_hotel(self, compan):
        _logger.info("DataBi: Calculating hotel names")
        dic_hotel = []  # Diccionario con el/los nombre de los hoteles
        dic_hotel.append({'ID_Hotel': compan.id_hotel,
                          'Descripcion': compan.property_name})
        return dic_hotel

    @api.model
    def data_bi_pais(self, compan):
        dic_pais = []
        # Diccionario con los nombre de los Paises usando los del INE
        dic_pais.append({'ID_Hotel': compan,
                         'ID_Pais': 'NONE',
                         'Descripcion': 'No Asignado'})
        paises = self.env['code.ine'].search_read([], ['code', 'name'])
        _logger.info("DataBi: Calculating %s countries", str(len(paises)))
        for pais in paises:
            dic_pais.append({'ID_Hotel': compan,
                             'ID_Pais': pais['code'],
                             'Descripcion': pais['name']})
        return dic_pais

    @api.model
    def data_bi_regimen(self, compan):
        dic_regimen = []  # Diccionario con los Board Services
        board_services = self.env['hotel.board.service'].search_read([])
        _logger.info("DataBi: Calculating %s board services", str(
                                                        len(board_services)))
        dic_regimen.append({'ID_Hotel': compan,
                            'ID_Regimen': 0,
                            'Descripcion': 'Sin régimen'})
        for board_service in board_services:
            dic_regimen.append({'ID_Hotel': compan,
                                'ID_Regimen': board_service['id'],
                                'Descripcion': board_service['name']})
        return dic_regimen

    @api.model
    def data_bi_estados(self, compan, estado_array):
        _logger.info("DataBi: Calculating all the states of the reserves")
        dic_estados = []  # Diccionario con los Estados Reserva
        estado_array_txt = ['Borrador', 'Confirmada', 'Hospedandose',
                            'Checkout', 'Cancelada']
        # estado_array = ['draft', 'confirm', 'booking', 'done', 'cancelled']
        for i in range(0, len(estado_array)):
            dic_estados.append({'ID_Hotel': compan,
                                'ID_EstadoReserva': i,
                                'Descripcion': estado_array_txt[i]})
        return dic_estados

    @api.model
    def data_bi_habitacione(self, compan, rooms):
        _logger.info("DataBi: Calculating %s room types", str(len(rooms)))
        dic_tipo_habitacion = []  # Diccionario con Rooms types
        for room in rooms:
            dic_tipo_habitacion.append({
                'ID_Hotel': compan,
                'ID_Tipo_Habitacion': room['id'],
                'Descripcion': room['name'],
                'Estancias': room['capacity']})
        return dic_tipo_habitacion

    @api.model
    def data_bi_capacidad(self, compan, rooms):
        _logger.info("DataBi: Calculating %s room capacity", str(len(rooms)))
        dic_capacidad = []  # Diccionario con las capacidades
        for room in rooms:
            dic_capacidad.append({
                'ID_Hotel': compan,
                'Hasta_Fecha':
                (date.today() + timedelta(days=365 * 3)).strftime("%Y-%m-%d"),
                'ID_Tipo_Habitacion': room['id'],
                'Nro_Habitaciones': room['total_rooms_count']})
        return dic_capacidad

    @api.model
    def data_bi_budget(self, compan):
        budgets = self.env['budget'].search([])
        _logger.info("DataBi: Calculating %s budget", str(len(budgets)))
        dic_budget = []  # Diccionario con las previsiones Budget
        for budget in budgets:
            dic_budget.append({'ID_Hotel': compan,
                               'Fecha': str(budget.year) + '-' +
                               str(budget.month).zfill(2) + '-01',
                               # 'ID_Tarifa': 0,
                               # 'ID_Canal': 0,
                               # 'ID_Pais': 0,
                               # 'ID_Regimen': 0,
                               # 'ID_Tipo_Habitacion': 0,
                               # 'ID_Cliente': 0,
                               'Room_Nights': budget.room_nights,
                               'Room_Revenue': budget.room_revenue,
                               # 'Pension_Revenue': 0,
                               'Estancias': budget.estancias})
        # Fecha fecha Primer día del mes
        # ID_Tarifa numérico Código de la Tarifa
        # ID_Canal numérico Código del Canal
        # ID_Pais numérico Código del País
        # ID_Regimen numérico Cóigo del Régimen
        # ID_Tipo_Habitacion numérico Código del Tipo de Habitación
        # iD_Segmento numérico Código del Segmento
        # ID_Cliente numérico Código del Cliente
        # Pension_Revenue numérico con dos decimales Ingresos por Pensión
        return dic_budget

    @api.model
    def data_bi_moti_bloq(self, compan):
        _logger.info("DataBi: Calculating all blocking reasons")
        dic_moti_bloq = []  # Diccionario con Motivo de Bloqueos
        bloqeo_array = ['Staff', _('Out of Service')]
        for i in range(0, len(bloqeo_array)):
            dic_moti_bloq.append({'ID_Hotel': compan,
                                  'ID_Motivo_Bloqueo': i,
                                  'Descripcion': bloqeo_array[i]})
        return dic_moti_bloq

    @api.model
    def data_bi_segment(self, compan):
        dic_segmentos = []  # Diccionario con Segmentación
        lineas = self.env['res.partner.category'].search([])
        _logger.info("DataBi: Calculating %s segmentations", str(len(lineas)))
        for linea in lineas:
            if linea.parent_id.name:
                seg_desc = linea.parent_id.name + " / " + linea.name
                dic_segmentos.append({'ID_Hotel': compan,
                                      'ID_Segmento': linea.id,
                                      'Descripcion': seg_desc})
        return dic_segmentos

    @api.model
    def data_bi_client(self, compan):
        dic_clientes = []  # Diccionario con Clientes (OTAs y agencias)
        dic_clientes.append({'ID_Hotel': compan,
                             'ID_Cliente': 0,
                             'Descripcion': u'Ninguno'})
        lineas = self.env['channel.ota.info'].search([])
        _logger.info("DataBi: Calculating %s otas", str(len(lineas)))

        for linea in lineas:
            dic_clientes.append({'ID_Hotel': compan,
                                 'ID_Cliente': linea.id,
                                 'Descripcion': linea.name})

        lineas = self.env['res.partner'].search([('is_tour_operator',
                                                '=', True)])
        id_cli_count = 700
        _logger.info("DataBi: Calculating %s Operators", str(len(lineas)))
        for linea in lineas:
            dic_clientes.append({'ID_Hotel': compan,
                                 'ID_Cliente': id_cli_count,
                                 'Descripcion': linea.name})
            id_cli_count += 1

        dic_clientes.append({'ID_Hotel': compan,
                             'ID_Cliente': 999,
                             'Descripcion': u'Web Propia'})
        dic_clientes.append({'ID_Hotel': compan,
                             'ID_Cliente': 901,
                             'Descripcion': u'Expedia Empaquedata'})
        dic_clientes.append({'ID_Hotel': compan,
                             'ID_Cliente': 902,
                             'Descripcion': u'Expedia Sin Comisión'})
        dic_clientes.append({'ID_Hotel': compan,
                             'ID_Cliente': 903,
                             'Descripcion': u'Puerta'})
        dic_clientes.append({'ID_Hotel': compan,
                             'ID_Cliente': 904,
                             'Descripcion': u'E-Mail'})
        dic_clientes.append({'ID_Hotel': compan,
                             'ID_Cliente': 905,
                             'Descripcion': u'Teléfono'})
        dic_clientes.append({'ID_Hotel': compan,
                             'ID_Cliente': 906,
                             'Descripcion': u'Call-Center'})
        dic_clientes.append({'ID_Hotel': compan,
                             'ID_Cliente': 907,
                             'Descripcion': u'Agencia'})
        dic_clientes.append({'ID_Hotel': compan,
                             'ID_Cliente': 908,
                             'Descripcion': u'Touroperador'})
        dic_clientes.append({'ID_Hotel': compan,
                             'ID_Cliente': 909,
                             'Descripcion': u'Virtual Door'})
        return dic_clientes

    @api.model
    def data_bi_bloqueos(self, compan, lines):
        dic_bloqueos = []  # Diccionario con Bloqueos
        lines = lines.filtered(
            lambda n: (n.reservation_id.reservation_type != 'normal') and (
                       n.reservation_id.state != 'cancelled'))
        _logger.info("DataBi: Calculating %s Bloqued", str(len(lines)))
        for line in lines:
            if line.reservation_id.reservation_type == 'out':
                id_m_b = 1
            else:
                id_m_b = 0
            dic_bloqueos.append({
                'ID_Hotel': compan,
                'Fecha_desde': line.date,
                'Fecha_hasta': (datetime.strptime(line.date, "%Y-%m-%d") +
                                timedelta(days=1)).strftime("%Y-%m-%d"),
                'ID_Tipo_Habitacion':
                    line.reservation_id.room_id.room_type_id.id,
                'ID_Motivo_Bloqueo': id_m_b,
                'Nro_Habitaciones': 1})
        return dic_bloqueos

    @api.model
    def data_bi_reservas(self, compan, lines, estado_array, dic_clientes):
        dic_reservas = []
        lineas = lines.filtered(
            lambda n:
                (n.reservation_id.reservation_type == 'normal') and
                (n.price > 0)
                )
        _logger.info("DataBi: Calculating %s reservations", str(len(lineas)))
        channels = {'door': 0,
                    'mail': 1,
                    'phone': 2,
                    'call': 3,
                    'web': 4,
                    'agency': 5,
                    'operator': 6,
                    'virtualdoor': 7}

        for linea in lineas:
            # _logger.info("DataBi: %s", linea.reservation_id.folio_id.name)

            id_segmen = 0
            if len(linea.reservation_id.segmentation_ids) > 0:
                id_segmen = linea.reservation_id.segmentation_ids[0].id
            elif len(linea.reservation_id.partner_id.category_id) > 0:
                id_segmen = (
                    linea.reservation_id.partner_id.category_id[0].id)
            precio_neto = linea.price
            precio_dto = 0
            precio_iva = 0
            precio_comision = 0

            if linea.reservation_id.ota_id.id:
                ota_prices = self.data_bi_comisiones_ota(linea)
                precio_neto = ota_prices[0]['precio_neto']
                precio_dto = ota_prices[0]['precio_dto']
                precio_iva = ota_prices[0]['precio_iva']
                precio_comision = ota_prices[0]['precio_comision']
            elif linea.reservation_id.channel_type == 'call':
                # Call Center. 7% comision
                precio_comision = (precio_neto*7/100)
                precio_neto -= precio_comision
                precio_iva = (precio_neto*10/100)
                precio_neto -= precio_iva
            else:
                precio_iva = round((precio_neto-(precio_neto/1.1)), 2)
                precio_neto -= precio_iva

            if (linea.discount != 0) or (linea.cancel_discount != 0):
                precio_dto = linea.price * ((linea.discount or 0.0) * 0.01)
                price = linea.price - precio_dto
                precio_dto += price * ((linea.cancel_discount or 0.0) * 0.01)

            dic_reservas.append({
                'ID_Reserva': linea.reservation_id.folio_id.id,
                'ID_Hotel': compan,
                'ID_EstadoReserva': estado_array.index(
                                                linea.reservation_id.state),
                'FechaVenta': linea.reservation_id.create_date[0:10],
                'ID_Segmento': id_segmen,
                'ID_Cliente': self.data_bi_channel_cli(linea, dic_clientes),
                'ID_Canal': channels[linea.reservation_id.channel_type],
                'FechaExtraccion': date.today().strftime('%Y-%m-%d'),
                'Entrada': linea.date,
                'Salida': (datetime.strptime(linea.date, "%Y-%m-%d") +
                           timedelta(days=1)).strftime("%Y-%m-%d"),
                'Noches': 1,
                'ID_TipoHabitacion': linea.reservation_id.room_type_id.id,
                'ID_HabitacionDuerme':
                    linea.reservation_id.room_id.room_type_id.id,
                'ID_Regimen': 0,
                'Adultos': linea.reservation_id.adults,
                'Menores': linea.reservation_id.children,
                'Cunas': 0,
                'PrecioDiario': precio_neto,
                'PrecioComision': precio_comision,
                'PrecioIva': precio_iva,
                'PrecioDto': precio_dto,
                'ID_Tarifa': linea.reservation_id.pricelist_id.id,
                'ID_Pais': self.data_bi_get_codeine(linea)
                })
        # ID_Reserva numérico Código único de la reserva
        # ID_Hotel numérico Código del Hotel
        # ID_EstadoReserva numérico Código del estado de la reserva
        # FechaVenta fecha Fecha de la venta de la reserva
        # ID_Segmento numérico Código del Segmento de la reserva
        # ID_Cliente Numérico Código del Cliente de la reserva
        # ID_Canal numérico Código del Canal
        # FechaExtraccion fecha Fecha de la extracción de los datos (Foto)
        # Entrada fecha Fecha de entrada
        # Salida fecha Fecha de salida
        # Noches numérico Nro. de noches de la reserva
        # ID_TipoHabitacion numérico Código del Tipo de Habitación
        # ID_Regimen numérico Código del Tipo de Régimen
        # Adultos numérico Nro. de adultos
        # Menores numérico Nro. de menores
        # Cunas numérico Nro. de cunas
        # PrecioDiario numérico con 2 decimales Precio por noche de la reserva
        # ID_Tarifa numérico Código de la tarifa aplicada a la reserva
        # ID_Pais numérico Código del país
        return dic_reservas

    @api.model
    def data_bi_channel_cli(self, reserva, dic_clientes):
        response = 0

        if reserva.reservation_id.channel_type == "door":
            response = 903
        elif reserva.reservation_id.channel_type == "mail":
            response = 904
        elif reserva.reservation_id.channel_type == "phone":
            response = 905
        elif reserva.reservation_id.channel_type == "call":
            response = 906
        elif reserva.reservation_id.channel_type == "virtualdoor":
            response = 909
        elif reserva.reservation_id.channel_type == "web":
            if reserva.reservation_id.ota_id.id:
                # OTA
                response = reserva.reservation_id.ota_id.id
            else:
                # Web Propia
                response = 999
        elif reserva.reservation_id.channel_type == "agency":
            tour = reserva.reservation_id.tour_operator_id
            if tour.name:
                mach = next((
                    l for l in dic_clientes if l['Descripcion'] == tour.name),
                                                                        False)
                response = mach['ID_Cliente']
            else:
                response = 907
        elif reserva.reservation_id.channel_type == "operator":
            tour = reserva.reservation_id.tour_operator_id
            if tour.name:
                mach = next((
                    l for l in dic_clientes if l['Descripcion'] == tour.name),
                                                                        False)
                response = mach['ID_Cliente']
            else:
                response = 908

        return response

    @api.model
    def data_bi_comisiones_ota(self, reserva):
        response_dic = []
        precio_neto = reserva.price
        precio_comision = 0
        precio_iva = 0
        precio_dto = 0
        if reserva.reservation_id.ota_id.ota_id == "2":
            # Booking. 15% comision
            precio_comision = (precio_neto*15/100)
            precio_neto -= precio_comision
            precio_iva = (precio_neto*10/100)
            precio_neto -= precio_iva

        elif reserva.reservation_id.ota_id.ota_id == "9":
            # Hotelbeds 20% comision
            precio_comision = (precio_neto*20/100)
            precio_neto -= precio_comision
            precio_iva = (precio_neto*10/100)
            precio_neto -= precio_iva

        elif reserva.reservation_id.ota_id.ota_id == "11":
            # HRS 20% comision
            precio_comision = (precio_neto*20/100)
            precio_neto -= precio_comision
            precio_iva = (precio_neto*10/100)
            precio_neto -= precio_iva

        elif reserva.reservation_id.ota_id.ota_id == "1":
            # Expedia.
            expedia_rate = self.data_bi_rate_expedia(reserva)

            # Odoo IVA discount
            precio_iva = precio_neto-(precio_neto/1.1)
            precio_neto -= precio_iva

            if (expedia_rate[3] == 'MERCHANT'):
                # EXPEDIA COLECT
                precio_comision = inv_percent(
                    precio_neto, expedia_rate[1]) - precio_neto
                precio_calculo = precio_neto + precio_comision
                # iva "interno" de expedia.....
                precio_iva2 = (precio_calculo*1.1) - precio_calculo
                precio_calculo += precio_iva2
                if expedia_rate[2] != 'NONE':
                    # FENCED MOD
                    # De enero a marzo: 7%
                    # De abril a 15 octubre: 5%
                    # De 16 octubre a 31 diciembre: 7%
                    fence_dto = 7
                    fence_dia = int(reserva.date[8:10])
                    fence_mes = int(reserva.date[5:7])
                    if (fence_mes >= 4) and (fence_mes <= 10):
                        fence_dto = 5
                        if (fence_dia > 15) and (fence_mes == 10):
                            fence_dto = 7
                    precio_dto += inv_percent(
                        precio_calculo, fence_dto) - precio_calculo
                # Corrector segundo iva...
                precio_dto += (precio_iva2 - precio_iva)

            else:
                precio_comision = inv_percent_inc(precio_neto, expedia_rate[1])
                precio_neto -= precio_comision

            # precio_neto = round(precio_neto, 2)
            # precio_comision = round(precio_comision, 2)
            # precio_iva = round(precio_iva, 2)
            # precio_dto = round(precio_dto, 2)
            # _logger.info("%s - %s - %s - %s - En Odoo:%s",
            #              reserva.reservation_id.folio_id.name,
            #              expedia_rate[0],
            #              expedia_rate[2],
            #              expedia_rate[3],
            #              reserva.price
            #              )
            # _logger.info('Neto: %s Comision: %s IVA: %s DTO: %s ',
            #              precio_neto,
            #              precio_comision,
            #              precio_iva,
            #              precio_dto)

        precio_neto = round(precio_neto, 2)
        precio_comision = round(precio_comision, 2)
        precio_iva = round(precio_iva, 2)
        precio_dto = round(precio_dto, 2)
        response_dic.append({'ota': reserva.reservation_id.ota_id.id,
                             'ota_id': reserva.reservation_id.ota_id.ota_id,
                             'precio_odoo': reserva.price,
                             'precio_neto': precio_neto,
                             'precio_comision': precio_comision,
                             'precio_iva': precio_iva,
                             'precio_dto': precio_dto,
                             })
        return response_dic

    @api.model
    def data_bi_rate_expedia(self, reserva):
        if datetime.strptime(reserva.reservation_id.folio_id.date_order[:10],
                             "%Y-%m-%d") < datetime(2019, 5, 9):
            comi_rate = 18
        else:
            comi_rate = self.env.user.company_id.expedia_rate
        json_rate = ''
        json_promo = 'NONE'
        json_pay_model = ''
        if reserva.reservation_id.channel_bind_ids.channel_raw_data:
            data = json.loads(
                reserva.reservation_id.channel_bind_ids.channel_raw_data)

            if data.get('channel_data')['pay_model'] is not None:
                json_pay_model = data.get('channel_data')['pay_model'].upper()
            else:
                _logger.critical("EXPEDIA NO pay_model: %s",
                                 reserva.reservation_id.folio_id.name,)
                json_pay_model = 'MERCHANT'

            if data.get('ancillary') is not None:
                json_rate = data.get('ancillary').get('Expedia Rates').upper()
                # _logger.info("EXPEDIA ANCILLARY 1 : %s - %s",
                #              json_rate,
                #              reserva.reservation_id.folio_id.name)

            else:
                jsonBooked = data['booked_rooms'][0]
                if jsonBooked.get('ancillary').get(
                        'channel_rate_name') is not None:
                    json_rate = jsonBooked.get('ancillary').get(
                        'channel_rate_name').upper()
                    # _logger.info("EXPEDIA ANCILLARY 2 : %s - %s",
                    #              json_rate,
                    #              reserva.reservation_id.folio_id.name)

                elif data.get('booked_rooms')[0].get(
                        'roomdays')[0].get('ancillary').get(
                                            'channel_rate_name') is not None:
                    json_rate = data.get(
                                'booked_rooms')[0].get(
                                'roomdays')[0].get(
                                'ancillary').get('channel_rate_name').upper()
                    json_promo = data.get(
                                'booked_rooms')[0].get(
                                'roomdays')[0].get(
                                'ancillary').get('promoName').upper()
                    # _logger.info("EXPEDIA ANCILLARY 3 : %s - %s",
                    #              json_rate,
                    #              reserva.reservation_id.folio_id.name)

                else:
                    _logger.critical("EXPEDIA Tarifa No Contemplada: %s",
                                     reserva.reservation_id.folio_id.name)
                    json_rate = 'ROOM ONLY'
        else:
            _logger.error("EXPEDIA NO RAW DATA: %s",
                          reserva.reservation_id.folio_id.name)
            json_rate = 'ROOM ONLY'

        if json_rate == '':
            _logger.critical("EXPEDIA Tarifa No Contemplada: %s",
                             reserva.reservation_id.folio_id.name)
            json_rate = 'ROOM ONLY'
        if json_promo == '':
            json_promo = 'NONE'
        return [json_rate, comi_rate, json_promo, json_pay_model]

    @api.model
    def data_bi_get_codeine(self, reserva):
        response = 'NONE'
        code = reserva.reservation_id.partner_id.code_ine_id
        if code:
            response = code.code
        else:
            for l in reserva.reservation_id.folio_id.checkin_partner_ids:
                if l.code_ine_id:
                    response = l.code_ine_id.code
        return response
        # Debug Stop -------------------
        # import wdb; wdb.set_trace()
        # Debug Stop -------------------
