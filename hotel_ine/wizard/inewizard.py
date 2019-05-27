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

from openerp import models, fields, api, _
import base64
import datetime
import calendar
import xml.etree.cElementTree as ET
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


def _get_default_date(option):
    now = datetime.datetime.now()
    month = int(now.month)-1
    year = int(now.year)
    if month <= 0:
        month = 12
        year -= year
    start_date = datetime.datetime(year, month, 1)
    end_date = calendar.monthrange(year, month)[1] - 1
    month_end_date = start_date + datetime.timedelta(days=end_date)
    if option == "start":
        return start_date
    return month_end_date


class Wizard(models.TransientModel):
    _name = 'ine.wizard'

    @api.onchange('ine_start')
    def onchange_ine_start(self):
        if self.ine_start > self.ine_end:
            self.ine_start = self.ine_end

    txt_filename = fields.Char()
    txt_binary = fields.Binary()
    ine_start = fields.Date("Fecha inicio", default=_get_default_date('start'))
    ine_end = fields.Date("Fecha final", default=_get_default_date('end'))

    adr_screen = fields.Char()
    rev_screen = fields.Char()

    @api.one
    def generate_file(self):

        compan = self.env.user.company_id
        message = ""
        if not compan.property_name:
            message = 'The NAME of the property is not established'
        if not compan.vat:
            message = 'The VAT of the property is not established'
        if message != "":
            raise UserError(message)
            return
        encuesta = ET.Element("ENCUESTA")
        cabezera = ET.SubElement(encuesta, "CABECERA")
        fecha = ET.SubElement(cabezera, "FECHA_REFERENCIA")
        ET.SubElement(fecha, "MES").text = self.ine_start[5:7]
        ET.SubElement(fecha, "ANYO").text = self.ine_start[0:4]
        ET.SubElement(cabezera, "DIAS_ABIERTO_MES_REFERENCIA").text = (
            str(int(self.ine_end[8:10]) - int(self.ine_start[8:10]) + 1))
        ET.SubElement(cabezera, "RAZON_SOCIAL").text = compan.name
        ET.SubElement(cabezera, "NOMBRE_ESTABLECIMIENTO").text = (
            compan.property_name)
        ET.SubElement(cabezera, "CIF_NIF").text = compan.vat[2:]
        ET.SubElement(cabezera, "NUMERO_REGISTRO").text = compan.tourism
        ET.SubElement(cabezera, "DIRECCION").text = compan.street
        ET.SubElement(cabezera, "CODIGO_POSTAL").text = compan.zip
        ET.SubElement(cabezera, "LOCALIDAD").text = compan.city
        ET.SubElement(cabezera, "MUNICIPIO").text = compan.city
        ET.SubElement(cabezera, "PROVINCIA"
                      ).text = compan.state_id.display_name
        ET.SubElement(cabezera, "TELEFONO_1").text = (
            compan.phone.replace(' ', '')[0:12])
        ET.SubElement(cabezera, "TIPO").text = compan.category_id.tipo
        ET.SubElement(cabezera, "CATEGORIA").text = compan.category_id.name
        # Debug Stop -------------------
        import wdb; wdb.set_trace()
        # Debug Stop -------------------
        active_room = self.env['hotel.room'].search_count(
            [('capacity', '>', 0)])
        ET.SubElement(cabezera, "HABITACIONES").text = str(active_room)
        ET.SubElement(cabezera, "PLAZAS_DISPONIBLES_SIN_SUPLETORIAS"
                      ).text = str(compan.seats)
        ET.SubElement(cabezera, "URL").text = compan.website
        alojamiento = ET.SubElement(encuesta, "ALOJAMIENTO")





        xmlstr = '<?xml version="1.0" encoding="ISO-8859-1"?>'
        xmlstr += ET.tostring(encuesta)
        return self.write({
             'txt_filename': 'INE_'+str(self.ine_month)+'_'+str(
                 self.ine_year) + '.' + 'xml',
             # 'adr_screen': _('ADR in the month of the survey: ')+str(
             #     round(month_adr_sum/month_adr_rooms, 2))+_('€ and '),
             # 'rev_screen': ' RevPar : '+str(round(
             #     month_adr_sum/month_revpar_staff_rooms, 2))+'€',
             'txt_binary': base64.encodestring(xmlstr)
             })
