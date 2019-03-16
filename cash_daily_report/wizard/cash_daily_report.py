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
import datetime
from datetime import datetime, date, time
import xlsxwriter
import base64
from odoo import api, fields, models, _
from openerp.exceptions import except_orm, UserError, ValidationError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class CashDailyReportWizard(models.TransientModel):
    FILENAME = 'cash_daily_report.xls'
    _name = 'cash.daily.report.wizard'

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
            'manager': u'Alexandre Díaz Cuadrado',
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

        worksheet = workbook.add_worksheet(_('Cash Daily Report'))

        worksheet.write('A1', _('Name'), xls_cell_format_header)
        worksheet.write('B1', _('Reference'), xls_cell_format_header)
        worksheet.write('C1', _('Client'), xls_cell_format_header)
        worksheet.write('D1', _('Date'), xls_cell_format_header)
        worksheet.write('E1', _('Journal'), xls_cell_format_header)
        worksheet.write('F1', _('Amount'), xls_cell_format_header)

        worksheet.set_column('C:C', 50)
        worksheet.set_column('D:D', 11)

        account_payments_obj = self.env['account.payment']
        account_payments = account_payments_obj.search([
            ('payment_date', '>=', self.date_start),
            ('payment_date', '<=', self.date_end),
        ])
        offset = 1
        total_account_payment_amount = 0.0
        for k_payment, v_payment in enumerate(account_payments):
            worksheet.write(k_payment+offset, 0, v_payment.name)
            worksheet.write(k_payment+offset, 1, v_payment.communication)
            worksheet.write(k_payment+offset, 2, v_payment.partner_id.name)
            worksheet.write(k_payment+offset, 3, v_payment.payment_date,
                            xls_cell_format_date)
            worksheet.write(k_payment+offset, 4, v_payment.journal_id.name)
            worksheet.write(k_payment+offset, 5, v_payment.amount,
                            xls_cell_format_money)
            total_account_payment_amount += v_payment.amount

        payment_returns_obj = self.env['payment.return']
        payment_returns = payment_returns_obj.search([
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
        ])
        offset += len(account_payments)
        total_payment_returns_amount = k_line = 0.0
        for k_payment, v_payment in enumerate(payment_returns):
            for k_line, v_line in enumerate(v_payment.line_ids):
                worksheet.write(k_line+offset, 0, v_payment.name)
                worksheet.write(k_line+offset, 1, v_line.reference)
                worksheet.write(k_line+offset, 2, v_line.partner_id.name)
                worksheet.write(k_line+offset, 3, v_payment.date,
                                xls_cell_format_date)
                worksheet.write(k_line+offset, 4, v_payment.journal_id.name)
                worksheet.write(k_line+offset, 5, -v_line.amount,
                                xls_cell_format_money)
                total_payment_returns_amount += v_line.amount
            offset += len(v_payment.line_ids)
        if total_account_payment_amount == 0 and total_payment_returns_amount == 0:
            raise UserError(_('Not Any Payments'))
        line = offset
        if k_line:
            line = k_line + offset
        if total_account_payment_amount > 0:
            line += 1
            worksheet.write(line, 4, _('TOTAL PAYMENTS'))
            worksheet.write(line, 5, total_account_payment_amount,
                            xls_cell_format_money)
        if total_payment_returns_amount > 0:
            line += 1
            worksheet.write(line, 4, _('TOTAL PAYMENT RETURNS'))
            worksheet.write(line, 5, -total_payment_returns_amount,
                            xls_cell_format_money)
        line += 1
        worksheet.write(line, 4, _('TOTAL'))
        worksheet.write(
            line,
            5,
            total_account_payment_amount - total_payment_returns_amount,
            xls_cell_format_money)

        workbook.close()
        file_data.seek(0)
        tnow = fields.Datetime.now().replace(' ', '_')
        return {
            'xls_filename': 'cash_daily_report_%s.xlsx' % tnow,
            'xls_binary': base64.encodestring(file_data.read()),
        }

    @api.multi
    def export(self):
        self.write(self._export())
        return {
            "type": "ir.actions.do_nothing",
        }
