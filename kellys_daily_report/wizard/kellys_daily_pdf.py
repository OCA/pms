# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2018 Jose Luis Algara Toledo <osotranquilo@gmail.com>
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
from datetime import datetime, date, time
from odoo import api, fields, models, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
# from odoo.tools import report

class KellysWizard(models.TransientModel):
    _name = 'kellysreport'

    @api.model
    def _get_default_habitaciones(self):
        return self.calculalimpiar(datetime.now())

    date_start = fields.Date("Fecha del listado", default=date.today())
    habitaciones = fields.Many2many('kellysrooms', string="Limpieza:",
                                    default=_get_default_habitaciones)
    order = fields.Selection([
        ('kelly ASC', 'Calendario'),
        ('kelly ASC, tipo ASC', 'Limpiar como... y orden en el Calendario'),
        ('kelly ASC, tipo ASC, checkin ASC',
         'Limpiar como... y Hora de entrada'),
        ], 'Orden de impresión',
        default='kelly ASC, tipo ASC, checkin ASC',
        required=True,
        help='Establece el orden en el que se imprimira el listado')

    @api.multi
    def calculate_report(self):
        self.habitaciones = self.calculalimpiar(
            datetime.strptime(self.date_start, "%Y-%m-%d"))
        return

    @api.multi
    def calculalimpiar(self, fechalimpieza=datetime.now()):
        dates = datetime.strftime(fechalimpieza, "%Y-%m-%d")
        grids = self.env['hotel.room'].search([], order='sequence ASC')
        grids2 = self.env['kellysrooms']
        listid = []
        for x in grids:
            rooms = self.env['hotel.reservation'].search(
                ['&', '&', ('checkin', '<=', dates),
                 ('checkout', '>=', dates),
                 ('state', '<>', 'cancelled'),
                 ('room_id', '=', x.id)
                 ], order='checkin ASC')

            tipos = False
            if len(rooms) != 0:
                if len(rooms) == 2:
                    tipos = 1
                    # Salida y etrada
                    checkinhour = rooms[1].checkin
                    checkouthour = rooms[1].checkout[:10]
                else:
                    if rooms[0].checkin[:10] == dates:
                        checkinhour = rooms[0].checkin
                        checkouthour = rooms[0].checkout[:10]
                        tipos = 3
                        # Revisar
                    elif rooms[0].checkout[:10] == dates:
                        checkinhour = 'no prevista'
                        checkouthour = ''
                        tipos = 1
                        # Salida
                    else:
                        checkinhour = rooms[0].checkin[:10]
                        checkouthour = rooms[0].checkout[:10]
                        tipos = 2
                        # Cliente
                        if rooms[0].reservation_type == 'staff':
                            checkinhour = rooms[0].checkin[:10]
                            checkouthour = rooms[0].checkout[:10]
                            tipos = 4
                            # Staff
                if rooms[0].reservation_type == 'out':
                    checkinhour = rooms[0].checkin[:10]
                    checkouthour = rooms[0].checkout[:10]
                    tipos = 5
                    # Averiada
            if tipos is not False:
                listid.append(grids2.create(
                    {'habitacion': rooms[0].room_id.name,
                     'habitacionid': rooms[0].room_id.id,
                     'tipo': tipos,
                     'notas': '',
                     'checkin': checkinhour,
                     # 'checkin': rooms[0].checkin[:10],
                     # 'checkout': rooms[0].checkout[:10],
                     'checkout': checkouthour,
                     # 'kelly': 5,
                     'clean_date': fechalimpieza
                     }).id)
        return self.env['kellysrooms'].search([('id', 'in', listid)])




# class ParticularReport(models.AbstractModel):
#     _name = 'report.module.report_name'
#     @api.model
#     def render_html(self, docids, data=None):
#         report_obj = self.env['report']
#         report = report_obj._get_report_from_name('module.report_name')
#         docargs = {
#             'doc_ids': docids,
#             'doc_model': report.model,
#             'docs': self,
#         }
#         return report_obj.render('module.report_name', docargs)

    @api.multi
    def print_rooms_report(self):
        rooms = self.env['kellysrooms'].search([('id', 'in',
                                                 self.habitaciones.ids)],
                                               order=self.order)
        docargs = {
            'doc_ids': rooms.ids,
            'doc_model': 'kellysrooms',
            'docs': self,
        }
        # Debug Stop -------------------
        #import wdb; wdb.set_trace()
        # Debug Stop -------------------

        # return self.env['report'].get_action(rooms, 'action_report_kellys')
        # return self.env['report'].get_action(rooms, 'report_action_kellysrooms')
        # return self.env.ref('kellys_daily_report.report_kellysrooms').report_action(self, rooms)
        # return self.env.ref('kellys_daily_report.report_kellysrooms').report_action(self, docargs)
        # return self.env.ref('kellys_daily_report.report_kellysrooms').report_action(rooms, docargs)
        return self.env.ref('kellys_daily_report.report_kellysrooms').report_action(rooms)
        # return {'type': 'ir.actions.report','report_kellysrooms': 'kellys_daily_report.template_kellysrooms','report_type':"qweb-pdf",'data': rooms,}
