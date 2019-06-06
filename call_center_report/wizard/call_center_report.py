# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018 Alexandre Díaz <dev@redneboa.es>
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
from io import BytesIO
from datetime import datetime, date
import xlsxwriter
import base64
from odoo import api, fields, models, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class CallCenterReportWizard(models.TransientModel):
    _name = 'call.center.report.wizard'

    @api.model
    def _get_default_date_start(self):
        return datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)

    @api.model
    def _get_default_date_end(self):
        return datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)

    date_start = fields.Date("Start Date", default=_get_default_date_start)
    date_end = fields.Date("End Date", default=_get_default_date_end)
    xls_filename = fields.Char()
    xls_binary = fields.Binary()

    @api.model
    def _export(self):
        date_format = "%d-%m-%Y"
        time_format = "%H:%M"
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data, {
            'strings_to_numbers': True,
            'default_date_format': 'dd/mm/yyyy'
        })

        company_id = self.env.user.company_id
        workbook.set_properties({
            'title': 'Exported data from ' + company_id.name,
            'subject': 'Payments Data from Odoo of ' + company_id.name,
            'author': 'Odoo',
            'manager': u'Call Center',
            'company': company_id.name,
            'category': 'Hoja de Calculo',
            'keywords': 'payments, odoo, data, ' + company_id.name,
            'comments': 'Created with Python in Odoo and XlsxWriter'})
        workbook.use_zip64()

        xls_cell_format_date = workbook.add_format({
            'num_format': 'dd/mm/yyyy'
        })
        xls_cell_format_money = workbook.add_format({
            'num_format': '#,##0.00'
        })
        xls_cell_format_header = workbook.add_format({
            'bg_color': '#CCCCCC'
        })

        worksheet = workbook.add_worksheet(_('Call Center Report - Production'))

        worksheet.write('A1', _('Ficha'), xls_cell_format_header)
        worksheet.write('B1', _('Fecha de Pedido'), xls_cell_format_header)
        worksheet.write('C1', _('Cliente'), xls_cell_format_header)
        worksheet.write('D1', _('Producto'), xls_cell_format_header)
        worksheet.write('E1', _('Noches/Uds'), xls_cell_format_header)
        worksheet.write('F1', _('Adultos'), xls_cell_format_header)
        worksheet.write('G1', _('Checkin'), xls_cell_format_header)
        worksheet.write('H1', _('In-Hora'), xls_cell_format_header)
        worksheet.write('I1', _('Checkout'), xls_cell_format_header)
        worksheet.write('J1', _('Creado por'), xls_cell_format_header)
        worksheet.write('K1', _('Total'), xls_cell_format_header)

        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 13)

        reservations_obj = self.env['hotel.reservation']
        reservations = reservations_obj.search([
            ('checkin', '>=', self.date_start),
            ('checkout', '<=', self.date_end),
            ('state', '=', 'done'),
            ('channel_type', '=', 'call'),
            ('folio_id.pending_amount', '<', 1),
        ])
        offset = 1
        total_reservation_amount = 0.0
        for k_res, v_res in enumerate(reservations):
            checkin_date = datetime.strptime(v_res.checkin, DEFAULT_SERVER_DATE_FORMAT)
            checkout_date = datetime.strptime(v_res.checkout, DEFAULT_SERVER_DATE_FORMAT)
            worksheet.write(k_res+offset, 0, v_res.folio_id.name)
            worksheet.write(k_res+offset, 1, v_res.folio_id.date_order,
                            xls_cell_format_date)
            worksheet.write(k_res+offset, 2, v_res.partner_id.name)
            worksheet.write(k_res+offset, 3, v_res.room_type_id.name)
            worksheet.write(k_res+offset, 4, v_res.nights)
            worksheet.write(k_res+offset, 5, v_res.adults)
            worksheet.write(k_res+offset, 6, checkin_date.strftime(date_format),
                            xls_cell_format_date)
            worksheet.write(k_res+offset, 7, v_res.arrival_hour)
            worksheet.write(k_res+offset, 8, checkout_date.strftime(date_format),
                            xls_cell_format_date)
            worksheet.write(k_res+offset, 9, v_res.create_uid.name)
            worksheet.write(k_res+offset, 10, v_res.price_total,
                            xls_cell_format_money)
            total_reservation_amount += v_res.price_total

        folio_ids = reservations.mapped('folio_id.id')
        folios = self.env['hotel.folio'].browse(folio_ids)
        services = self.env['hotel.service'].browse()
        for folio in folios:
            services += folio.service_ids.filtered(lambda r:
                r.channel_type == 'call' and r.folio_id.pending_amount < 1)
        offset += len(reservations)
        total_service_amount = k_line = 0.0
        for k_service, v_service in enumerate(services):
            worksheet.write(k_service+offset, 0, v_service.folio_id.name)
            worksheet.write(k_service+offset, 1, v_service.folio_id.date_order,
                            xls_cell_format_date)
            worksheet.write(k_service+offset, 2, v_service.folio_id.partner_id.name)
            worksheet.write(k_service+offset, 3, v_service.product_id.name)
            worksheet.write(k_service+offset, 4, v_service.product_qty)
            worksheet.write(k_service+offset, 5, '')
            worksheet.write(k_service+offset, 6, '')
            worksheet.write(k_service+offset, 7, '')
            worksheet.write(k_service+offset, 8, '')
            worksheet.write(k_service+offset, 9, v_service .create_uid.name)
            worksheet.write(k_service+offset, 10, v_service.price_total,
                            xls_cell_format_money)
            total_service_amount += v_service.price_total
        offset += len(services)
        #~ if total_reservation_amount == 0 and total_service_amount == 0:
            #~ raise UserError(_('No Hay reservas de Call Center'))
        line = offset
        if k_line:
            line = k_line + offset
        if total_reservation_amount > 0:
            line += 1
            worksheet.write(line, 9, _('TOTAL RESERVAS'))
            worksheet.write(line, 10, total_reservation_amount,
                            xls_cell_format_money)
        if total_service_amount > 0:
            line += 1
            worksheet.write(line, 9, _('TOTAL SERVICIOS'))
            worksheet.write(line, 10, total_service_amount,
                            xls_cell_format_money)
        line += 1
        worksheet.write(line, 9, _('TOTAL'))
        worksheet.write(line, 10    , total_reservation_amount + total_service_amount,
            xls_cell_format_money)

        worksheet = workbook.add_worksheet(_('Call Center Report - Sales'))

        worksheet.write('A1', _('Estado'), xls_cell_format_header)
        worksheet.write('B1', _('Ficha'), xls_cell_format_header)
        worksheet.write('C1', _('Fecha de Pedido'), xls_cell_format_header)
        worksheet.write('D1', _('Cliente'), xls_cell_format_header)
        worksheet.write('E1', _('Producto'), xls_cell_format_header)
        worksheet.write('F1', _('Noches/Uds'), xls_cell_format_header)
        worksheet.write('G1', _('Adultos'), xls_cell_format_header)
        worksheet.write('H1', _('Checkin'), xls_cell_format_header)
        worksheet.write('I1', _('In-Hora'), xls_cell_format_header)
        worksheet.write('J1', _('Checkout'), xls_cell_format_header)
        worksheet.write('K1', _('Creado por'), xls_cell_format_header)
        worksheet.write('L1', _('Total'), xls_cell_format_header)

        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 13)

        reservations_obj = self.env['hotel.reservation']
        reservations = reservations_obj.search([
            ('folio_id.date_order', '>=', self.date_start),
            ('folio_id.date_order', '<=', self.date_end),
            ('channel_type','=','call'),
        ])
        offset = 1
        total_reservation_amount = 0.0
        for k_res, v_res in enumerate(reservations):
            checkin_date = datetime.strptime(v_res.checkin, DEFAULT_SERVER_DATE_FORMAT)
            checkout_date = datetime.strptime(v_res.checkout, DEFAULT_SERVER_DATE_FORMAT)
            worksheet.write(k_res+offset, 0, v_res.state)
            worksheet.write(k_res+offset, 1, v_res.folio_id.name)
            worksheet.write(k_res+offset, 2, v_res.folio_id.date_order,
                            xls_cell_format_date)
            worksheet.write(k_res+offset, 3, v_res.partner_id.name)
            worksheet.write(k_res+offset, 4, v_res.room_type_id.name)
            worksheet.write(k_res+offset, 5, v_res.nights)
            worksheet.write(k_res+offset, 6, v_res.adults)
            worksheet.write(k_res+offset, 7, checkin_date.strftime(date_format),
                            xls_cell_format_date)
            worksheet.write(k_res+offset, 8, v_res.arrival_hour)
            worksheet.write(k_res+offset, 9, checkout_date.strftime(date_format),
                            xls_cell_format_date)
            worksheet.write(k_res+offset, 10, v_res.create_uid.name)
            worksheet.write(k_res+offset, 11, v_res.price_total,
                            xls_cell_format_money)
            total_reservation_amount += v_res.price_total

        folio_ids = reservations.mapped('folio_id.id')
        folios = self.env['hotel.folio'].browse(folio_ids)
        services = self.env['hotel.service'].browse()
        for folio in folios:
            services += folio.service_ids.filtered(lambda r:
                r.channel_type == 'call' and r.folio_id.pending_amount < 1)
        offset += len(reservations)
        total_service_amount = k_line = 0.0
        for k_service, v_service in enumerate(services):
            worksheet.write(k_service+offset, 1, v_service.folio_id.state)
            worksheet.write(k_service+offset, 1, v_service.folio_id.name)
            worksheet.write(k_service+offset, 2, v_service.folio_id.date_order,
                            xls_cell_format_date)
            worksheet.write(k_service+offset, 3, v_service.folio_id.partner_id.name)
            worksheet.write(k_service+offset, 4, v_service.product_id.name)
            worksheet.write(k_service+offset, 5, v_service.product_qty)
            worksheet.write(k_service+offset, 6, '')
            worksheet.write(k_service+offset, 7, '')
            worksheet.write(k_service+offset, 8, '')
            worksheet.write(k_service+offset, 9, '')
            worksheet.write(k_service+offset, 10, v_service .create_uid.name)
            worksheet.write(k_service+offset, 11, v_service.price_total,
                            xls_cell_format_money)
            total_service_amount += v_service.price_total
        offset += len(services)
        #~ if total_reservation_amount == 0 and total_service_amount == 0:
            #~ raise UserError(_('No Hay reservas de Call Center'))
        line = offset
        if k_line:
            line = k_line + offset
        if total_reservation_amount > 0:
            line += 1
            worksheet.write(line, 10, _('TOTAL RESERVAS'))
            worksheet.write(line, 11, total_reservation_amount,
                            xls_cell_format_money)
        if total_service_amount > 0:
            line += 1
            worksheet.write(line, 10, _('TOTAL SERVICIOS'))
            worksheet.write(line, 11, total_service_amount,
                            xls_cell_format_money)
        line += 1
        worksheet.write(line, 10, _('TOTAL'))
        worksheet.write(line, 11    , total_reservation_amount + total_service_amount,
            xls_cell_format_money)

        worksheet = workbook.add_worksheet(_('Call Center Report - Cancelations'))

        worksheet.write('A1', _('Estado'), xls_cell_format_header)
        worksheet.write('B1', _('Ficha'), xls_cell_format_header)
        worksheet.write('C1', _('Fecha de Pedido'), xls_cell_format_header)
        worksheet.write('D1', _('Cliente'), xls_cell_format_header)
        worksheet.write('E1', _('Producto'), xls_cell_format_header)
        worksheet.write('F1', _('Noches/Uds'), xls_cell_format_header)
        worksheet.write('G1', _('Adultos'), xls_cell_format_header)
        worksheet.write('H1', _('Checkin'), xls_cell_format_header)
        worksheet.write('I1', _('In-Hora'), xls_cell_format_header)
        worksheet.write('J1', _('Checkout'), xls_cell_format_header)
        worksheet.write('K1', _('Creado por'), xls_cell_format_header)
        worksheet.write('K1', _('Cancelado en'), xls_cell_format_header)
        worksheet.write('L1', _('Precio Final'), xls_cell_format_header)
        worksheet.write('M1', _('Precio Original'), xls_cell_format_header)

        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 13)

        reservations_obj = self.env['hotel.reservation']
        reservations = reservations_obj.search([
            ('last_updated_res', '>=', self.date_start),
            ('last_updated_res', '<=', self.date_end),
            ('channel_type','=','call'),
            ('state','=','cancelled'),
        ])
        offset = 1
        total_reservation_amount = 0.0
        for k_res, v_res in enumerate(reservations):
            checkin_date = datetime.strptime(v_res.checkin, DEFAULT_SERVER_DATE_FORMAT)
            checkout_date = datetime.strptime(v_res.checkout, DEFAULT_SERVER_DATE_FORMAT)
            worksheet.write(k_res+offset, 0, v_res.state)
            worksheet.write(k_res+offset, 1, v_res.folio_id.name)
            worksheet.write(k_res+offset, 2, v_res.folio_id.date_order,
                            xls_cell_format_date)
            worksheet.write(k_res+offset, 3, v_res.partner_id.name)
            worksheet.write(k_res+offset, 4, v_res.room_type_id.name)
            worksheet.write(k_res+offset, 5, v_res.nights)
            worksheet.write(k_res+offset, 6, v_res.adults)
            worksheet.write(k_res+offset, 7, checkin_date.strftime(date_format),
                            xls_cell_format_date)
            worksheet.write(k_res+offset, 8, v_res.arrival_hour)
            worksheet.write(k_res+offset, 9, checkout_date.strftime(date_format),
                            xls_cell_format_date)
            worksheet.write(k_res+offset, 10, v_res.create_uid.name)
            worksheet.write(k_res+offset, 9, v_res.last_updated_res,
                            xls_cell_format_date)
            worksheet.write(k_res+offset, 11, v_res.price_total,
                            xls_cell_format_money)
            worksheet.write(k_res+offset, 12, v_res.price_total - v_res.discount,
                            xls_cell_format_money)
            total_reservation_amount += v_res.price_total

        offset += len(reservations)

        #~ if total_reservation_amount == 0 and total_service_amount == 0:
            #~ raise UserError(_('No Hay reservas de Call Center'))
        line = offset
        if k_line:
            line = k_line + offset
        if total_reservation_amount > 0:
            line += 1
            worksheet.write(line, 11, _('TOTAL RESERVAS'))
            worksheet.write(line, 12, total_reservation_amount,
                            xls_cell_format_money)

        workbook.close()
        file_data.seek(0)
        tnow = fields.Datetime.now().replace(' ', '_')
        return {
            'xls_filename': 'call_%s.xlsx' %self.env.user.company_id.property_name,
            'xls_binary': base64.encodestring(file_data.read()),
        }

    @api.multi
    def export(self):
        self.write(self._export())
        return {
            "type": "ir.actions.do_nothing",
        }
