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
import xlsxwriter
import base64
from odoo import api, fields, models, _


class GlassofExporterWizard(models.TransientModel):
    FILENAME = 'invoices_glasof.xls'
    _name = 'glasof.exporter.wizard'

    date_start = fields.Date("Start Date")
    date_end = fields.Date("End Date")
    export_journals = fields.Boolean("Export Account Movements?", default=True)
    export_invoices = fields.Boolean("Export Invoices?", default=True)
    seat_num = fields.Integer("Seat Number Start", default=1)
    xls_journals_filename = fields.Char()
    xls_journals_binary = fields.Binary()
    xls_invoices_filename = fields.Char()
    xls_invoices_binary = fields.Binary()

    @api.model
    def _export_journals(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data, {
            'strings_to_numbers': True,
            'default_date_format': 'dd/mm/yyyy'
        })

        company_id = self.env.user.company_id
        workbook.set_properties({
            'title': 'Exported data from ' + company_id.name,
            'subject': 'PMS Data from Odoo of ' + company_id.name,
            'author': 'Odoo ALDA PMS',
            'manager': 'Jose Luis Algara',
            'company': company_id.name,
            'category': 'Hoja de Calculo',
            'keywords': 'pms, odoo, alda, data, ' + company_id.name,
            'comments': 'Created with Python in Odoo and XlsxWriter'})
        workbook.use_zip64()

        xls_cell_format_seat = workbook.add_format({'num_format': '#'})
        xls_cell_format_date = workbook.add_format({
            'num_format': 'dd/mm/yyyy'
        })
        xls_cell_format_saccount = workbook.add_format({
            'num_format': '000000'
        })
        xls_cell_format_money = workbook.add_format({
            'num_format': '#,##0.00'
        })
        xls_cell_format_header = workbook.add_format({
            'bg_color': '#CCCCCC'
        })

        worksheet = workbook.add_worksheet('Simples-1')

        worksheet.write('A1', _('Seat'), xls_cell_format_header)
        worksheet.write('B1', _('Date'), xls_cell_format_header)
        worksheet.write('C1', _('SubAccount'), xls_cell_format_header)
        worksheet.write('D1', _('Description'), xls_cell_format_header)
        worksheet.write('E1', _('Concept'), xls_cell_format_header)
        worksheet.write('F1', _('Debit'), xls_cell_format_header)
        worksheet.write('G1', _('Credit'), xls_cell_format_header)
        worksheet.write('H1', _('Seat Type'), xls_cell_format_header)

        worksheet.set_column('B:B', 11)
        worksheet.set_column('E:E', 50)

        account_move_obj = self.env['account.move']
        account_moves = account_move_obj.search([
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
        ])
        start_seat = self.seat_num
        nrow = 1
        for move in account_moves:
            nmove = True
            for line in move.line_ids:
                if line.journal_id.type in ('cash', 'bank'):
                    worksheet.write(nrow, 0, nmove and start_seat or '',
                                    xls_cell_format_seat)
                    worksheet.write(nrow, 1, nmove and line.date or '',
                                    xls_cell_format_date)
                    worksheet.write(nrow, 2, line.account_id.code,
                                    xls_cell_format_saccount)
                    worksheet.write(nrow, 3, '')
                    worksheet.write(nrow, 4, line.ref and line.ref[:50] or '')
                    worksheet.write(nrow, 5, line.debit, xls_cell_format_money)
                    worksheet.write(nrow, 6, line.credit,
                                    xls_cell_format_money)
                    worksheet.write(nrow, 7, '')
                    nmove = False
                    nrow += 1
            start_seat += 1

        workbook.close()
        file_data.seek(0)
        tnow = fields.Datetime.now().replace(' ', '_')
        return {
            'xls_journals_filename': 'journals_glasof_%s.xlsx' % tnow,
            'xls_journals_binary': base64.encodestring(file_data.read()),
        }

    @api.model
    def _export_invoices(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data, {
            'strings_to_numbers': True,
            'default_date_format': 'dd/mm/yyyy'
        })

        company_id = self.env.user.company_id
        workbook.set_properties({
            'title': 'Exported data from ' + company_id.name,
            'subject': 'PMS Data from Odoo of ' + company_id.name,
            'author': 'Odoo ALDA PMS',
            'manager': 'Jose Luis Algara',
            'company': company_id.name,
            'category': 'Hoja de Calculo',
            'keywords': 'pms, odoo, alda, data, ' + company_id.name,
            'comments': 'Created with Python in Odoo and XlsxWriter'})
        workbook.use_zip64()

        xls_cell_format_seat = workbook.add_format({'num_format': '#'})
        xls_cell_format_date = workbook.add_format({
            'num_format': 'dd/mm/yyyy'
        })
        xls_cell_format_saccount = workbook.add_format({
            'num_format': '000000'
        })
        xls_cell_format_money = workbook.add_format({
            'num_format': '#,##0.00'
        })
        xls_cell_format_odec = workbook.add_format({
            'num_format': '#,#0.0'
        })
        xls_cell_format_header = workbook.add_format({
            'bg_color': '#CCCCCC'
        })

        worksheet = workbook.add_worksheet('ventas')

        account_inv_obj = self.env['account.invoice']
        account_invs = account_inv_obj.search([
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
        ])

        nrow = 1
        for inv in account_invs:
            if inv.partner_id.parent_id:
                firstname = inv.partner_id.parent_id.firstname or ''
                lastname = inv.partner_id.parent_id.lastname or ''
            else:
                firstname = inv.partner_id.firstname or ''
                lastname = inv.partner_id.lastname or ''
                
            worksheet.write(nrow, 0, inv.number)
            worksheet.write(nrow, 1, inv.date_invoice, xls_cell_format_date)
            worksheet.write(nrow, 2, '')
            worksheet.write(nrow, 3, inv.partner_id.vat and
                            inv.partner_id.vat[:2] or '')
            worksheet.write(nrow, 4, inv.partner_id.vat and
                            inv.partner_id.vat[2:] or '')
            worksheet.write(nrow, 5, lastname)
            worksheet.write(nrow, 6, '')
            worksheet.write(nrow, 7, firstname)
            worksheet.write(nrow, 8, 705.0, xls_cell_format_odec)
            worksheet.write(nrow, 9, inv.amount_untaxed, xls_cell_format_money)
            if any(inv.tax_line_ids):
                worksheet.write(nrow,
                                10,
                                inv.tax_line_ids[0].tax_id.amount,
                                xls_cell_format_money)
            else:
                worksheet.write(nrow, 10, '')
            worksheet.write(nrow, 11, inv.tax_line_ids and
                            inv.tax_line_ids[0].amount or '',
                            xls_cell_format_money)
            worksheet.write(nrow, 12, '')
            worksheet.write(nrow, 13, '')
            worksheet.write(nrow, 14, '')
            worksheet.write(nrow, 15, '')
            worksheet.write(nrow, 16, '')
            worksheet.write(nrow, 17, '')
            worksheet.write(nrow, 18, '')
            worksheet.write(nrow, 19, '')
            worksheet.write(nrow, 20, '')
            worksheet.write(nrow, 21, 'S')
            worksheet.write(nrow, 22, '')
            if inv.type == 'out_refund':
                worksheet.write(nrow, 23, inv.origin)
            else:
                worksheet.write(nrow, 23, '')
            worksheet.write(nrow, 24, '')
            worksheet.write(nrow, 25, '')
            worksheet.write(nrow, 27, '')
            worksheet.write(nrow, 28, '')
            worksheet.write(nrow, 29, '')
            worksheet.write(nrow, 30, '')
            worksheet.write(nrow, 31, '')
            worksheet.write(nrow, 32, '')
            worksheet.write(nrow, 33, '')
            worksheet.write(nrow, 34, '')
            worksheet.write(nrow, 35, '')
            worksheet.write(nrow, 36, '')
            worksheet.write(nrow, 37, '')
            worksheet.write(nrow, 38, '')
            worksheet.write(nrow, 39, '')
            worksheet.write(nrow, 40, '')
            worksheet.write(nrow, 41, '')
            worksheet.write(nrow, 42, '')
            worksheet.write(nrow, 43, '430')
            nrow += 1

        workbook.add_worksheet('compras')
        workbook.close()
        file_data.seek(0)
        tnow = fields.Datetime.now().replace(' ', '_')
        return {
            'xls_invoices_filename': 'invoices_glasof_%s.xlsx' % tnow,
            'xls_invoices_binary': base64.encodestring(file_data.read()),
        }

    @api.multi
    def export(self):
        towrite = {}
        if self.export_journals:
            towrite.update(self._export_journals())
        if self.export_invoices:
            towrite.update(self._export_invoices())
        if any(towrite):
            self.write(towrite)
        return {
            "type": "ir.actions.do_nothing",
        }
