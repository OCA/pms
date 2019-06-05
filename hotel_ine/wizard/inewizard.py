# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017-19 Alda Hotels <informatica@aldahotels.com>
#                          Jose Luis Algara <osotranquilo@gmail.com>
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
import base64
import datetime
import calendar
import xml.etree.cElementTree as ET
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


def get_years():
    year_list = []
    for i in range(2017, get_year()+1):
        year_list.append((i, str(i)))
    return year_list


def get_year():
    now = datetime.datetime.now()
    return int(now.year)


def get_month():
    now = datetime.datetime.now()
    month = int(now.month)-1
    if month <= 0:
        month = 12
    return month


class Wizard(models.TransientModel):
    _name = 'ine.wizard'

    txt_filename = fields.Char()
    txt_binary = fields.Binary()

    ine_month = fields.Selection([(1, 'January'), (2, 'February'),
                                  (3, 'March'), (4, 'April'),
                                  (5, 'May'), (6, 'June'), (7, 'July'),
                                  (8, 'August'), (9, 'September'),
                                  (10, 'October'), (11, 'November'),
                                  (12, 'December'), ],
                                 string='Month', default=get_month())
    ine_year = fields.Selection(get_years(), default=get_year(), string='Year')

    adr_screen = fields.Char()
    rev_screen = fields.Char()

    @api.one
    def generate_file(self):
        _logger.warning("Start Export INE XML file")
        last_day = calendar.monthrange(self.ine_year, self.ine_month)[1]
        ine_start_search = datetime.date(self.ine_year, self.ine_month, 1)
        ine_end_search = ine_start_search + datetime.timedelta(days=last_day)
        compan = self.env.user.company_id
        active_room = self.env['hotel.room'].search([('in_ine', '=', True)])
        message = ""
        if not compan.property_name:
            message = 'The NAME of the property is not established'
        if not compan.name:
            message = 'The NAME of the company is not established'
        if not compan.vat:
            message = 'The VAT is not established'
        if not compan.ine_tourism:
            message = 'The tourism number of the property is not established'
        if message != "":
            raise UserError(message)
            return
        encuesta = ET.Element("ENCUESTA")
        cabezera = ET.SubElement(encuesta, "CABECERA")
        fecha = ET.SubElement(cabezera, "FECHA_REFERENCIA")
        ET.SubElement(fecha, "MES").text = "%02d" % (self.ine_month)
        ET.SubElement(fecha, "ANYO").text = str(self.ine_year)
        ET.SubElement(cabezera, "DIAS_ABIERTO_MES_REFERENCIA").text = (
            str(last_day))
        ET.SubElement(cabezera, "RAZON_SOCIAL").text = compan.name
        ET.SubElement(cabezera, "NOMBRE_ESTABLECIMIENTO").text = (
            compan.property_name)
        ET.SubElement(cabezera, "CIF_NIF").text = compan.vat[2:].strip()
        ET.SubElement(cabezera, "NUMERO_REGISTRO").text = compan.ine_tourism
        ET.SubElement(cabezera, "DIRECCION").text = compan.street
        ET.SubElement(cabezera, "CODIGO_POSTAL").text = compan.zip
        ET.SubElement(cabezera, "LOCALIDAD").text = compan.city
        ET.SubElement(cabezera, "MUNICIPIO").text = compan.city
        ET.SubElement(cabezera, "PROVINCIA"
                      ).text = compan.state_id.display_name
        ET.SubElement(cabezera, "TELEFONO_1").text = (
            compan.phone.replace(' ', '')[0:12])
        ET.SubElement(cabezera, "TIPO").text = (
            compan.ine_category_id.category_type)
        ET.SubElement(cabezera, "CATEGORIA").text = compan.ine_category_id.name

        ET.SubElement(cabezera, "HABITACIONES").text = str(len(active_room))
        ET.SubElement(cabezera, "PLAZAS_DISPONIBLES_SIN_SUPLETORIAS"
                      ).text = str(compan.ine_seats)
        ET.SubElement(cabezera, "URL").text = compan.website
        alojamiento = ET.SubElement(encuesta, "ALOJAMIENTO")

        all_room_nights = self.env['hotel.reservation.line'].search([
            ('date', '>=', ine_start_search),
            ('date', '<=', ine_end_search),
            ('reservation_id.room_id.in_ine', '=', True),
            ('reservation_id.state', '!=', "cancelled"),
            ('reservation_id.reservation_type', '=', 'normal'),
            ])
        room_nights = all_room_nights.filtered(
                    lambda n: (self.get_codeine(n.reservation_id)))

        # Creating the empty dictionary system
        dic_tabla = []
        for room_night in room_nights:
            ine_code = self.get_codeine(room_night.reservation_id)
            if not next((item for item in dic_tabla if item["ine"] == ine_code), False):
                for x in range(1, last_day+1):
                    dic_tabla.append({'ine': ine_code,
                                      'dia': x,
                                      'entradas': 0,
                                      'salidas': 0,
                                      'pernocta': 0
                                      })

        # Adding overnight stays per day and INE code
        pernocta_total = []
        for dia in range(1, last_day+1):
            pernocta_total.append(0)
            for room_night in room_nights.filtered(
                    lambda x: x.date == str(self.ine_year)+'-'+str(
                    self.ine_month).zfill(2)+'-'+str(dia).zfill(2)):
                ine_code = self.get_codeine(room_night.reservation_id)
                for idx, val in enumerate(dic_tabla):
                    if val['ine'] == ine_code and val['dia'] == dia:
                        dic_tabla[idx]['pernocta'] += room_night.reservation_id.adults

        # Calculating outputs and entries
        last_stay = 0
        for idx, row in enumerate(dic_tabla):
            if dic_tabla[idx]['dia'] == 1:
                last_stay = 0

            if last_stay < dic_tabla[idx]['pernocta']:
                dic_tabla[idx]['entradas'] += dic_tabla[idx]['pernocta'] - last_stay
            elif last_stay > dic_tabla[idx]['pernocta']:
                dic_tabla[idx]['salidas'] += last_stay - dic_tabla[idx][
                                                                    'pernocta']
            # _logger.warning("%s: %s Perenocta: %s In: %s Out: %s Last=%s", dic_tabla[idx]['ine'], dic_tabla[idx]['dia'], dic_tabla[idx]['pernocta'], dic_tabla[idx]['entradas'], dic_tabla[idx]['salidas'],last_stay)
            last_stay = dic_tabla[idx]['pernocta']
            pernocta_total[(dic_tabla[idx]['dia'])-1] += dic_tabla[idx]['pernocta']

        # "Print" outputs and entries
        ine_residen = ""
        for idx, row in enumerate(dic_tabla):
            if ine_residen != dic_tabla[idx]['ine']:
                ine_residen = dic_tabla[idx]['ine']
                residencia = ET.SubElement(alojamiento, "RESIDENCIA")
                if len(dic_tabla[idx]['ine']) > 3:
                    ET.SubElement(residencia, "ID_PROVINCIA_ISLA"
                                  ).text = str(dic_tabla[idx]['ine'])
                else:
                    ET.SubElement(residencia, "ID_PAIS"
                                  ).text = str(dic_tabla[idx]['ine'])
            if ((dic_tabla[idx]['entradas'] != 0)
                    or (dic_tabla[idx]['salidas'] != 0)
                    or (dic_tabla[idx]['pernocta'] != 0)):
                movimiento = ET.SubElement(residencia, "MOVIMIENTO")
                ET.SubElement(movimiento, "N_DIA").text = (
                                                "%02d" % dic_tabla[idx]['dia'])
                ET.SubElement(movimiento, "ENTRADAS").text = str(
                                                    dic_tabla[idx]['entradas'])
                ET.SubElement(movimiento, "SALIDAS").text = str(
                                                    dic_tabla[idx]['salidas'])
                ET.SubElement(movimiento, "PERNOCTACIONES").text = str(
                                                    dic_tabla[idx]['pernocta'])

        habitaciones = ET.SubElement(encuesta, "HABITACIONES")
        # Bucle de HABITACIONES_MOVIMIENTO

        ingresos = 0
        habitaci = 0
        hab_vend = 0
        for dia in range(1, last_day+1):
            suple = 0
            doble = 0
            dindi = 0
            otras = 0

            habitaci += len(active_room)
            habitaci -= self.env['hotel.reservation.line'].search([
                ('date', '=', str(self.ine_year)+'-'+str(
                    self.ine_month).zfill(2)+'-'+str(dia).zfill(2)),
                ('reservation_id.reservation_type', '!=', 'normal'),
                ], count=True)
            for room_night in room_nights.filtered(lambda x: x.date == str(
                                            self.ine_year)+'-'+str(
                                            self.ine_month).zfill(2)+'-'+str(
                                            dia).zfill(2)):
                ingresos += room_night.price
                hab_vend += 1

                if room_night.reservation_id.room_id.capacity == 2:
                    if room_night.reservation_id.adults == 1:
                        dindi += 1
                    else:
                        doble += 1
                else:
                    otras += 1
                if len(room_night.reservation_id.service_ids):
                    for service in room_night.reservation_id.service_ids:
                        if service.product_id.is_extra_bed:
                            suple += 1

            # Here, we correct the extra beds
            if pernocta_total[dia-1] > suple + compan.ine_seats:
                suple = pernocta_total[dia-1] - compan.ine_seats

            habitaciones_m = ET.SubElement(habitaciones,
                                           "HABITACIONES_MOVIMIENTO")
            ET.SubElement(habitaciones_m,
                          "HABITACIONES_N_DIA").text = "%02d" % (dia)
            ET.SubElement(habitaciones_m,
                          "PLAZAS_SUPLETORIAS").text = str(suple)
            ET.SubElement(habitaciones_m,
                          "HABITACIONES_DOBLES_USO_DOBLE").text = str(doble)
            ET.SubElement(habitaciones_m,
                          "HABITACIONES_DOBLES_USO_INDIVIDUAL").text = str(
                                                                        dindi)
            ET.SubElement(habitaciones_m,
                          "HABITACIONES_OTRAS").text = str(otras)

        precios = ET.SubElement(encuesta, "PRECIOS")
        ET.SubElement(precios,
                      "REVPAR_MENSUAL").text = str(round(ingresos/habitaci, 2))
        ET.SubElement(precios,
                      "ADR_MENSUAL").text = str(round(ingresos/hab_vend, 2))
        ET.SubElement(precios, "ADR_TOUROPERADOR_TRADICIONAL").text = '0'
        ET.SubElement(precios,
                      "PCTN_HABITACIONES_OCUPADAS_TOUROPERADOR_TRADICIONAL"
                      ).text = '0'
        ET.SubElement(precios,
                      "ADR_TOUROPERADOR_ONLINE").text = '0'
        ET.SubElement(precios,
                      "PCTN_HABITACIONES_OCUPADAS_TOUROPERADOR_ONLINE"
                      ).text = '0'
        ET.SubElement(precios,
                      "ADR_EMPRESAS").text = '0'
        ET.SubElement(precios,
                      "PCTN_HABITACIONES_OCUPADAS_EMPRESAS").text = '0'
        ET.SubElement(precios,
                      "ADR_AGENCIA_DE_VIAJE_TRADICIONAL").text = '0'
        ET.SubElement(precios,
                      "PCTN_HABITACIONES_OCUPADAS_AGENCIA_TRADICIONAL"
                      ).text = '0'
        ET.SubElement(precios, "ADR_AGENCIA_DE_VIAJE_ONLINE").text = '0'
        ET.SubElement(precios,
                      "PCTN_HABITACIONES_OCUPADAS_AGENCIA_ONLINE"
                      ).text = '0'
        ET.SubElement(precios, "ADR_PARTICULARES").text = '0'
        ET.SubElement(precios,
                      "PCTN_HABITACIONES_OCUPADAS_PARTICULARES").text = '0'
        ET.SubElement(precios,
                      "ADR_GRUPOS").text = '0'
        ET.SubElement(precios,
                      "PCTN_HABITACIONES_OCUPADAS_GRUPOS").text = '0'
        ET.SubElement(precios, "ADR_INTERNET").text = '0'
        ET.SubElement(precios,
                      "PCTN_HABITACIONES_OCUPADAS_INTERNET").text = '0'
        ET.SubElement(precios, "ADR_OTROS").text = '0'
        ET.SubElement(precios,
                      "PCTN_HABITACIONES_OCUPADAS_OTROS").text = '0'

        personal = ET.SubElement(encuesta, "PERSONAL_OCUPADO")
        ET.SubElement(personal, "PERSONAL_NO_REMUNERADO").text = '0'
        ET.SubElement(personal,
                      "PERSONAL_REMUNERADO_FIJO").text = str(
                          compan.ine_permanent_staff)
        ET.SubElement(personal,
                      "PERSONAL_REMUNERADO_EVENTUAL").text = str(
                      compan.ine_eventual_staff)

        xmlstr = '<?xml version="1.0" encoding="ISO-8859-1"?>'
        xmlstr += ET.tostring(encuesta).decode('utf-8')
        return self.write({
             'txt_filename': 'INE_'+str(self.ine_month)+'_'+str(
                                                self.ine_year) + '.' + 'xml',
             'adr_screen': 'ADR en el mes de la encuesta: '+str(
                 round(ingresos/habitaci, 2)) + '€ y ',
             'rev_screen': ' RevPar : '+str(round(ingresos/hab_vend, 2))+'€',
             'txt_binary': base64.encodestring(xmlstr.encode())
             })

    @api.model
    def get_codeine(self, reserva):
        response = False
        code = reserva[0].partner_id.code_ine_id
        if code:
            response = code.code
        else:
            for l in reserva[0].folio_id.checkin_partner_ids:
                if l.code_ine_id:
                    response = l.code_ine_id.code
        return response
