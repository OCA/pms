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
        worksheet.write('C1', _('Client/Supplier'), xls_cell_format_header)
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
        total_account_payment = 0.0
        total_account_expenses = 0.0
        payment_journals = {}
        expense_journals = {}
        total_dates = {}
        for k_payment, v_payment in enumerate(account_payments):
            where = v_payment.partner_id.name
            amount = v_payment.amount if v_payment.payment_type in ('inbound') \
                else -v_payment.amount
            if v_payment.payment_type == 'transfer':
                where = v_payment.destination_journal_id.name
                total_account_payment += -amount
                if v_payment.destination_journal_id.name not in payment_journals:
                    payment_journals.update({v_payment.destination_journal_id.name: -amount})
                else:
                    payment_journals[v_payment.destination_journal_id.name] += -amount
                if v_payment.payment_date not in total_dates:
                    total_dates.update({v_payment.payment_date: {v_payment.destination_journal_id.name: -amount}})
                else:
                    if v_payment.destination_journal_id.name not in total_dates[v_payment.payment_date]:
                        total_dates[v_payment.payment_date].update({v_payment.destination_journal_id.name: -amount})
                    else:
                        total_dates[v_payment.payment_date][v_payment.destination_journal_id.name] += -amount
            if amount < 0:
                total_account_expenses += -amount
                if v_payment.journal_id.name not in expense_journals:
                    expense_journals.update({v_payment.journal_id.name: amount})
                else:
                    expense_journals[v_payment.journal_id.name] += amount
                if v_payment.payment_date not in total_dates:
                    total_dates.update({v_payment.payment_date: {v_payment.journal_id.name: amount}})
                else:
                    if v_payment.journal_id.name not in total_dates[v_payment.payment_date]:
                        total_dates[v_payment.payment_date].update({v_payment.journal_id.name: amount})
                    else:
                        total_dates[v_payment.payment_date][v_payment.journal_id.name] += amount
            else:
                total_account_payment += amount
                if v_payment.journal_id.name not in payment_journals:
                    payment_journals.update({v_payment.journal_id.name: amount})
                else:
                    payment_journals[v_payment.journal_id.name] += amount
                if v_payment.payment_date not in total_dates:
                    total_dates.update({v_payment.payment_date: {v_payment.journal_id.name: amount}})
                else:
                    if v_payment.journal_id.name not in total_dates[v_payment.payment_date]:
                        total_dates[v_payment.payment_date].update({v_payment.journal_id.name: amount})
                    else:
                        total_dates[v_payment.payment_date][v_payment.journal_id.name] += amount

            worksheet.write(k_payment+offset, 0, v_payment.name)
            worksheet.write(k_payment+offset, 1, v_payment.communication)
            worksheet.write(k_payment+offset, 2, where)
            worksheet.write(k_payment+offset, 3, v_payment.payment_date,
                            xls_cell_format_date)
            worksheet.write(k_payment+offset, 4, v_payment.journal_id.name)
            worksheet.write(k_payment+offset, 5, amount,
                            xls_cell_format_money)
            total_account_payment_amount += amount

        payment_returns_obj = self.env['payment.return']
        payment_returns = payment_returns_obj.search([
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
        ])
        offset += len(account_payments)
        total_payment_returns_amount = k_line = 0.0
        return_journals = {}
        for k_payment, v_payment in enumerate(payment_returns):
            for k_line, v_line in enumerate(v_payment.line_ids):
                if v_payment.journal_id.name not in return_journals:
                    return_journals.update({v_payment.journal_id.name: -v_line.amount})
                else:
                    return_journals[v_payment.journal_id.name] += -v_line.amount

                if v_payment.date not in total_dates:
                    total_dates.update({v_payment.date: {v_payment.journal_id.name: -v_line.amount}})
                else:
                    if v_payment.journal_id.name not in total_dates[v_payment.date]:
                        total_dates[v_payment.date].update({v_payment.journal_id.name: -v_line.amount})
                    else:
                        total_dates[v_payment.date][v_payment.journal_id.name] += -v_line.amount

                worksheet.write(k_line+offset, 0, v_payment.name)
                worksheet.write(k_line+offset, 1, v_line.reference)
                worksheet.write(k_line+offset, 2, v_line.partner_id.name)
                worksheet.write(k_line+offset, 3, v_payment.date,
                                xls_cell_format_date)
                worksheet.write(k_line+offset, 4, v_payment.journal_id.name)
                worksheet.write(k_line+offset, 5, -v_line.amount,
                                xls_cell_format_money)
                total_payment_returns_amount += -v_line.amount
            offset += len(v_payment.line_ids)
        if total_account_payment_amount == 0 and total_payment_returns_amount == 0:
            raise UserError(_('Not Any Payments'))
        line = offset
        if k_line:
            line = k_line + offset


        result_journals = {}
        # NORMAL PAYMENTS
        if total_account_payment != 0:
            line += 1
            worksheet.write(line, 4, _('TOTAL PAYMENTS'), xls_cell_format_header)
            worksheet.write(line, 5, total_account_payment,
                            xls_cell_format_header)
        for journal in payment_journals:
            line += 1
            worksheet.write(line, 4, _(journal))
            worksheet.write(line, 5, payment_journals[journal],
                            xls_cell_format_money)
            if journal not in result_journals:
                result_journals.update({journal: payment_journals[journal]})
            else:
                result_journals[journal] += payment_journals[journal]

        # RETURNS
        if total_payment_returns_amount != 0:
            line += 1
            worksheet.write(line, 4, _('TOTAL PAYMENT RETURNS'), xls_cell_format_header)
            worksheet.write(line, 5, total_payment_returns_amount,
                            xls_cell_format_header)
        for journal in return_journals:
            line += 1
            worksheet.write(line, 4, _(journal))
            worksheet.write(line, 5, return_journals[journal],
                            xls_cell_format_money)
            if journal not in result_journals:
                result_journals.update({journal: return_journals[journal]})
            else:
                result_journals[journal] += return_journals[journal]

        # EXPENSES
        if total_account_expenses != 0:
            line += 1
            worksheet.write(line, 4, _('TOTAL EXPENSES'), xls_cell_format_header)
            worksheet.write(line, 5, -total_account_expenses,
                            xls_cell_format_header)
        for journal in expense_journals:
            line += 1
            worksheet.write(line, 4, _(journal))
            worksheet.write(line, 5, -expense_journals[journal],
                            xls_cell_format_money)
            if journal not in result_journals:
                result_journals.update({journal: expense_journals[journal]})
            else:
                result_journals[journal] += expense_journals[journal]

        #TOTALS
        line += 1
        worksheet.write(line, 4, _('TOTAL'), xls_cell_format_header)
        worksheet.write(
            line,
            5,
            total_account_payment + total_payment_returns_amount - total_account_expenses,
            xls_cell_format_header)
        for journal in result_journals:
            line += 1
            worksheet.write(line, 4, _(journal))
            worksheet.write(line, 5, result_journals[journal],
                            xls_cell_format_money)

        worksheet = workbook.add_worksheet(_('Por dia'))
        worksheet.write('A1', _('Date'), xls_cell_format_header)
        columns = ('B1','C1','D1','E1','F1','G1','H1')
        i = 0
        column_journal = {}
        for journal in result_journals:
            worksheet.write(columns[i], _(journal), xls_cell_format_header)
            i += 1
            column_journal.update({journal: i})

        worksheet.set_column('C:C', 50)
        worksheet.set_column('D:D', 11)

        offset = 1
        total_dates = sorted(total_dates.items(), key=lambda x: x[0])
        for k_day, v_day in enumerate(total_dates):
            worksheet.write(k_day+offset, 0, v_day[0])
            for journal in v_day[1]:
                worksheet.write(k_day+offset, column_journal[journal], v_day[1][journal])

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
