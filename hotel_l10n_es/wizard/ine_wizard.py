# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Alda Hotels <informatica@aldahotels.com>
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

from odoo import models, fields, api, _
import base64
import datetime
import calendar
import xml.etree.cElementTree as ET
from openerp.exceptions import UserError



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


class IneWizard(models.TransientModel):
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
        month_first_date = datetime.datetime(self.ine_year, self.ine_month, 1)
        last_day = calendar.monthrange(self.ine_year, self.ine_month)[1] - 1
        month_end_date = month_first_date + datetime.timedelta(days=last_day)
        m_f_d_search = datetime.date(self.ine_year, self.ine_month, 1)
        m_e_d_search = m_f_d_search + datetime.timedelta(days=last_day)
        last_day += 1

        # Seleccionamos los que tienen Entrada en el mes + salida en el mes +
        # entrada antes y salida despues. Ordenandolos.
        lines = self.env['hotel.checkin.partner'].search(
            ['|', '|', '&', ('exit_date', '>=', m_f_d_search),
             ('exit_date', '<=', m_e_d_search), '&',
             ('enter_date', '>=', m_f_d_search),
             ('enter_date', '<=', m_e_d_search), '&',
             ('enter_date', '<=', m_f_d_search),
             ('exit_date', '>=', m_e_d_search)], order="enter_date")
        lines = lines.sorted(
            key=lambda r: str(r.partner_id.code_ine)+r.enter_date)

        if len(lines) > 0:

            company = self.env.user.company_id

            encuesta = ET.Element("ENCUESTA")
            cabezera = ET.SubElement(encuesta, "CABECERA")
            fecha = ET.SubElement(cabezera, "FECHA_REFERENCIA")
            ET.SubElement(fecha, "MES").text = '{:02d}'.format(self.ine_month)
            ET.SubElement(fecha, "ANYO").text = str(self.ine_year)
            month_end_date = (
                datetime.datetime(self.ine_year, self.ine_month, 1) +
                datetime.timedelta(days=calendar.monthrange(
                    self.ine_year, self.ine_month)[1] - 1))
            ET.SubElement(cabezera, "DIAS_ABIERTO_MES_REFERENCIA").text = (
                str(month_end_date.day))
            ET.SubElement(cabezera, "RAZON_SOCIAL").text = company.name
            ET.SubElement(cabezera, "NOMBRE_ESTABLECIMIENTO").text = (
                company.property_name)
            ET.SubElement(cabezera, "CIF_NIF").text = company.vat[2:]
            ET.SubElement(cabezera, "NUMERO_REGISTRO").text = company.ine_tourism
            ET.SubElement(cabezera, "DIRECCION").text = company.street
            ET.SubElement(cabezera, "CODIGO_POSTAL").text = company.zip
            ET.SubElement(cabezera, "LOCALIDAD").text = company.city
            ET.SubElement(cabezera, "MUNICIPIO").text = company.city
            ET.SubElement(cabezera, "PROVINCIA"
                          ).text = company.state_id.display_name
            ET.SubElement(cabezera, "TELEFONO_1").text = (
                company.phone.replace(' ', '')[0:12])
            ET.SubElement(cabezera, "TIPO").text = company.ine_category_id.category_type
            ET.SubElement(cabezera, "CATEGORIA").text = company.ine_category_id.name
            active_room = self.env['hotel.room'].search_count(
                [('capacity', '>', 0)])
            ET.SubElement(cabezera, "HABITACIONES").text = str(active_room)
            ET.SubElement(cabezera, "PLAZAS_DISPONIBLES_SIN_SUPLETORIAS"
                          ).text = str(company.seats)
            ET.SubElement(cabezera, "URL").text = company.website
            alojamiento = ET.SubElement(encuesta, "ALOJAMIENTO")
            # Bucle de RESIDENCIA

            # Init Variables
            ine_entrada = []
            ine_salidas = []
            ine_pernoct = []
            ine_pernoct_total = []
            for x in range(last_day+1):
                ine_entrada.append(0)
                ine_salidas.append(0)
                ine_pernoct.append(0)
                ine_pernoct_total.append(0)

            # Cabezera
            code_control = lines[0].partner_id.code_ine_id.code

            if code_control is False:
                _logger.error('Usuario sin codigo de INE: ' +
                              lines[0].partner_id.name)
                raise UserError(_('ERROR: Usuario sin codigo de INE: '
                                  + lines[0].partner_id.name))

            for line in lines:
                # Si ha cambiado el codigo
                if code_control != line.partner_id.code_ine_id.code:
                    residencia = ET.SubElement(alojamiento, "RESIDENCIA")
                    if len(code_control) > 3:
                        ET.SubElement(residencia, "ID_PROVINCIA_ISLA"
                                      ).text = str(code_control)
                    else:
                        ET.SubElement(residencia, "ID_PAIS"
                                      ).text = str(code_control)

                    for x in range(1, last_day+1):
                        if ine_entrada[x]+ine_salidas[x]+ine_pernoct[x] > 0:
                            movimiento = ET.SubElement(residencia,
                                                       "MOVIMIENTO")
                            ET.SubElement(movimiento, "N_DIA"
                                          ).text = "%02d" % (x)
                            ET.SubElement(movimiento, "ENTRADAS"
                                          ).text = str(ine_entrada[x])
                            ET.SubElement(movimiento, "SALIDAS"
                                          ).text = str(ine_salidas[x])
                            ET.SubElement(movimiento, "PERNOCTACIONES"
                                          ).text = str(ine_pernoct[x])
                            # Guardamos el total de pernoctaciones/dia
                            ine_pernoct_total[x] += ine_pernoct[x]

                    # Reset Variables
                    ine_entrada = []
                    ine_salidas = []
                    ine_pernoct = []
                    for x in xrange(last_day+1):
                        ine_entrada.append(0)
                        ine_salidas.append(0)
                        ine_pernoct.append(0)

                    code_control = line.partner_id.code_ine_id.code

                # Hacemos las sumas
                f_entrada = line.enter_date.split('-')
                f_salida = line.exit_date.split('-')
                # Ha entrado este mes
                if int(f_entrada[1]) == self.ine_month:
                    ine_entrada[int(f_entrada[2])] += 1
                    cuenta_entrada = int(f_entrada[2])
                else:
                    # No marco entrada y cuento desde el dia 1
                    cuenta_entrada = 1
                # Ha salido este mes
                if int(f_salida[1]) == self.ine_month:
                    ine_salidas[int(f_salida[2])] += 1
                    cuenta_salida = int(f_salida[2])
                else:
                    # No marco entrada y cuento desde el dia 1
                    cuenta_salida = last_day+1
                # Contando pernoctaciones
                for i in range(cuenta_salida-cuenta_entrada):
                    ine_pernoct[cuenta_entrada+i] += 1
            # Fin de cuenta desde Cardex

            habitaciones = ET.SubElement(encuesta, "HABITACIONES")
            # Bucle de HABITACIONES_MOVIMIENTO

            month_adr_sum = 0
            month_adr_rooms = 0
            month_revpar_staff_rooms = 0
            movimientos = []

            # Reset Variables
            ine_entrada = []
            ine_salidas = []
            for x in range(last_day+1):
                ine_entrada.append(0)
                ine_salidas.append(0)

            for x in range(last_day+1):
                movimientos.append([0, 0, 0, 0, 0, 0, active_room])
                # movimientos.append(['suple','doble','indi','otra','adr_sum',
                # 'adr_rum','adr_staff'])

            lines_res = self.env['hotel.reservation'].search(
                ['|', '|', '&', ('checkout', '>=', str(m_f_d_search)),
                 ('checkout', '<=', str(m_e_d_search)), '&',
                 ('checkin', '>=', str(m_f_d_search)),
                 ('checkin', '<=', str(m_e_d_search)), '&',
                 ('checkin', '<=', str(m_f_d_search)),
                 ('checkout', '>=', str(m_e_d_search))], order="checkin")
            for line_res in lines_res:
                room = self.env['hotel.room'].search([(
                    'product_id', '=', line_res.product_id.id)])
                # No es Staff o Out y esta booking
                if (line_res.reservation_type == 'normal') and (
                    (line_res.state == 'booking') or (
                        line_res.state == 'done')):

                    # calculamos capacidad de habitacion
                    # !!!!! ATENCION !!!!
                    # pendiente de añadir un campo con las supletorias.
                    # asumimos de momento que por defecto supletorias sera
                    # 0 por ejemplo para todas......
                    # cambiar/calcular la siguiente linea.
                    suple_room = 0

                    capacidad = room.capacity + suple_room

                    # Cuadramos adultos con los checkin realizados.
                    if line_res.adults > line_res.cardex_count:
                        adultos = line_res.cardex_count
                    else:
                        adultos = line_res.adults

                    f_entrada = line_res.checkin.split('-')
                    f_salida = line_res.checkout.split('-')
                    f_entrada[2] = f_entrada[2].split()[0]
                    f_salida[2] = f_salida[2].split()[0]

                    # Ha entrado este mes
                    if int(f_entrada[1]) == self.ine_month:
                        ine_entrada[int(f_entrada[2])] += 1
                        cuenta_entrada = int(f_entrada[2])
                    else:
                        # No marco entrada y cuento desde el dia 1
                        cuenta_entrada = 1
                    # Ha salido este mes?
                    if int(f_salida[1]) == self.ine_month:
                        ine_salidas[int(f_salida[2])] += 1
                        cuenta_salida = int(f_salida[2])
                    else:
                        # No marco salida y cuento hasta el dia last_day
                        cuenta_salida = last_day + 1

                    # para las noches que ha estado
                    for dia_x in range(cuenta_entrada, cuenta_salida+1):
                        # si no supera el numero de habitaciones ni de
                        # pernoctaciones totales del dia...
                        if ((movimientos[dia_x-1][1]+movimientos[dia_x-1][2] +
                             movimientos[dia_x-1][3]) < active_room and (
                                 ((movimientos[dia_x-1][1]*2) +
                                  movimientos[dia_x-1][2] +
                                  movimientos[dia_x-1][3]) <
                                 ine_pernoct_total[dia_x-1])):
                            if capacidad == 1:
                                # Habitacion Individual
                                movimientos[dia_x-1][3] += 1
                                if adultos > 1:
                                    # Supletorias
                                    movimientos[dia_x-1][0] += 1
                            elif capacidad == 2:
                                # Habitacion Doble
                                if adultos == 1:
                                    # Uso individual
                                    movimientos[dia_x-1][2] += 1
                                else:
                                    # Doble
                                    movimientos[dia_x-1][1] += 1
                                    if adultos > 2:
                                        # Doble + supletorias
                                        movimientos[dia_x-1][0] += (adultos-2)
                            elif capacidad > 2:
                                # Otras Habitaciones
                                movimientos[dia_x-1][3] += 1
                        else:
                            _logger.info(str(dia_x) +
                                         'Exceso de habitaciones ' +
                                         str(line_res) + ' ' + line_res.name +
                                         ' ' + line_res.partner_id.name +
                                         ' PERNOCT.: ' +
                                         str(ine_pernoct_total[dia_x-1]))

                    # ADR y RevPar
                    for xx_lines in line_res.reservation_lines:
                        # ADR calculo
                        xx_dia = xx_lines.date.split('-')
                        if int(xx_dia[1]) == self.ine_month:
                            movimientos[int(xx_dia[2])][4] += xx_lines.price
                            movimientos[int(xx_dia[2])][5] += 1

                else:
                    # Staff o Out
                    for xx_lines in line_res.reservation_lines:
                        xx_dia = xx_lines.date.split('-')
                        if int(xx_dia[1]) == self.ine_month:
                            # Restamos una Habitacion no valida para RevPar
                            movimientos[int(xx_dia[2])][6] -= 1

            for dia_x in xrange(1, last_day+1):
                # Si la suma de los durmiendo es superior a pernoctaciones INE
                suma_durmiendo = ((movimientos[dia_x][1]*2)
                                  + movimientos[dia_x][2]
                                  + movimientos[dia_x][3])
                if suma_durmiendo > ine_pernoct_total[dia_x]:
                    suma_durmiendo = (suma_durmiendo -
                                      ine_pernoct_total[dia_x])
                    if suma_durmiendo == 1:
                        if movimientos[dia_x][2] > 0:
                            # quitamos una individual
                            movimientos[dia_x][2] -= 1
                        elif movimientos[dia_x][3] > 0:
                            # quitamos una otras
                            movimientos[dia_x][3] -= 1
                    elif suma_durmiendo == 2:
                        if movimientos[dia_x][1] > 0:
                            # quitamos una doble
                            movimientos[dia_x][1] -= 1
                        elif movimientos[dia_x][3] > 0:
                            # quitamos una otras
                            movimientos[dia_x][3] -= 1
                habitaciones_m = ET.SubElement(habitaciones,
                                               "HABITACIONES_MOVIMIENTO")
                ET.SubElement(habitaciones_m,
                              "HABITACIONES_N_DIA").text = "%02d" % (dia_x)
                if ine_pernoct_total[dia_x] > company.seats:
                    # Añadimos Supletorias por si excedemos plazas
                    movimientos[dia_x][0] = (ine_pernoct_total[dia_x]
                                             - company.seats)
                    _logger.info(' Dia: ' + str(dia_x) +
                                 ' [ADD] Supletorias a : ' +
                                 str(movimientos[dia_x][0]))
                ET.SubElement(habitaciones_m,
                              "PLAZAS_SUPLETORIAS").text = str(
                                  movimientos[dia_x][0])
                ET.SubElement(habitaciones_m,
                              "HABITACIONES_DOBLES_USO_DOBLE").text = str(
                                  movimientos[dia_x][1])
                ET.SubElement(habitaciones_m,
                              "HABITACIONES_DOBLES_USO_INDIVIDUAL").text = str(
                                  movimientos[dia_x][2])
                ET.SubElement(habitaciones_m,
                              "HABITACIONES_OTRAS").text = str(
                                  movimientos[dia_x][3])

                # calculo ADR
                month_adr_sum += movimientos[dia_x][4]
                month_adr_rooms += movimientos[dia_x][5]
                month_revpar_staff_rooms += movimientos[dia_x][6]

            precios = ET.SubElement(encuesta, "PRECIOS")
            ET.SubElement(precios,
                          "REVPAR_MENSUAL").text = str(
                              round(month_adr_sum/month_revpar_staff_rooms, 2))
            ET.SubElement(precios,
                          "ADR_MENSUAL").text = str(
                              round(month_adr_sum/month_adr_rooms, 2))
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
                              company.permanentstaff)
            ET.SubElement(personal,
                          "PERSONAL_REMUNERADO_EVENTUAL").text = str(
                              company.eventualstaff)

            xmlstr = '<?xml version="1.0" encoding="ISO-8859-1"?>'
            xmlstr += ET.tostring(encuesta)
            # file=base64.encodestring( xmlstr )
            return self.write({
                 'txt_filename': 'INE_'+str(self.ine_month)+'_'+str(
                     self.ine_year) + '.' + 'xml',
                 'adr_screen': _('ADR in the month of the survey: ')+str(
                     round(month_adr_sum/month_adr_rooms, 2))+_('€ and '),
                 'rev_screen': ' RevPar : '+str(round(
                     month_adr_sum/month_revpar_staff_rooms, 2))+'€',
                 'txt_binary': base64.encodestring(xmlstr)
                 })
        else:
            return self.write({
                 'rev_screen': _('No data in this month')
                 })

