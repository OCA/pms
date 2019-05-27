# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018 Alda Hotels <informatica@aldahotels.com>
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

from odoo import models, fields, api
import base64
import datetime
from odoo.tools.translate import _
import unidecode


class PoliceWizard(models.TransientModel):
    _name = 'police.wizard'

    download_date = fields.Date('Date', required=True)
    download_num = fields.Char('Correlative number', required=True, size=3,
                               help='Number provided by the police')
    txt_filename = fields.Char()
    txt_binary = fields.Binary()
    txt_message = fields.Char()
    log_police = fields.Char()
    error_partner = fields.Many2one('res.partner')

    @api.one
    def generate_file(self):
        company = self.env.user.company_id
        if company.police_number is not False and company.property_name is not False:
            lines = self.env['hotel.checkin.partner'].search([
                ('enter_date', '=', self.download_date),
                ('state', 'in', ('booking', 'done')),
                ])
            content = "1|"+company.police_number+"|"+company.property_name.upper()[0:40]
            content += "|"
            content += datetime.datetime.now().strftime("%Y%m%d|%H%M")
            content += "|"+str(len(lines)) + """
"""
            log_police = 0
            for line in lines:
                if ((line.partner_id.document_type is not False)
                        and (line.partner_id.document_number is not False)
                        and (line.partner_id.firstname is not False)
                        and (line.partner_id.gender is not False)
                        and (line.partner_id.lastname is not False)):

                    log_police += 1
                    if len(line.partner_id.code_ine_id.code) == 5:
                        content += "2|"+line.partner_id.document_number.upper(
                            ) + "||"
                    else:
                        content += "2||"+line.partner_id.document_number.upper(
                            ) + "|"
                    content += line.partner_id.document_type + "|"
                    content += datetime.datetime.strptime(
                        line.partner_id.document_expedition_date,
                        "%Y-%m-%d").date().strftime("%Y%m%d") + "|"
                    firstname = line.partner_id.firstname
                    if 'ñ' not in firstname and 'Ñ' not in firstname:
                        firstname = unidecode.unidecode(firstname)
                    lastname = line.partner_id.lastname.split()
                    for i, string in enumerate(lastname):
                        if 'ñ' not in string and 'Ñ' not in string:
                            lastname[i] = unidecode.unidecode(string)
                    if len(lastname) >= 2:
                        content += lastname[0].upper() + "|"
                        lastname.pop(0)
                        for string in lastname:
                            content += string.upper() + " "
                        content = content[:len(content) - 1]
                    else:
                        content += lastname[0].upper() + "|"
                    content += "|"
                    content += firstname.upper() + "|"
                    content += line.partner_id.gender.upper()[0] + "|"
                    content += datetime.datetime.strptime(
                        line.partner_id.birthdate_date,
                        "%Y-%m-%d").date().strftime("%Y%m%d") + "|"
                    if len(line.partner_id.code_ine_id.code) == 5:
                        content += u'ESPAÑA|'
                    else:
                        content += line.partner_id.code_ine_id.name.upper()[0:21]
                        content += "|"
                    content += datetime.datetime.strptime(
                        line.enter_date,
                        "%Y-%m-%d").date().strftime("%Y%m%d") + "|"
                    content += """
"""
                else:
                    self.error_partner = line.partner_id

                    return self.write({
                        'error_partner': line.partner_id.id,
                        'txt_message': _('Problem generating the file. \
                                         Checkin without data, \
                                         or incorrect data: ')})
            log_police = str(log_police) + _(' records added from ')
            log_police += str(len(lines)) + _(' records processed.')
            return self.write({
                'txt_filename': company.police_number + '.' + self.download_num,
                'log_police': log_police,
                'txt_message': _(
                    'Generated file. Download it and give it to the police.'),
                'txt_binary': base64.encodestring(content.encode("iso-8859-1"))
                })
        return self.write({
            'txt_message': _('File not generated by configuration error.')
        })
