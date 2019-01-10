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
from openerp import models, fields, api, _
from odoo.osv.expression import get_unaccent_wrapper


class ResPartner(models.Model):
    _inherit = 'res.partner'

    document_type = fields.Selection([
        ('D', 'DNI'),
        ('P', 'Pasaporte'),
        ('C', 'Permiso de Conducir'),
        ('I', 'Carta o Doc. de Identidad'),
        ('N', 'Permiso Residencia Español'),
        ('X', 'Permiso Residencia Europeo')],
        help=_('Select a valid document type'),
        default='D',
        string='Doc. type',
        )
    document_number = fields.Char('Document number')
    document_expedition_date = fields.Date('Document expedition date')

    code_ine_id = fields.Many2one('code.ine',
        help=_('Country or province of origin. Used for INE statistics.'))

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        result = super(ResPartner, self).name_search(name, args=None,
                                                     operator='ilike',
                                                     limit=100)
        if args is None:
            args = []
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            self.check_access_rights('read')
            where_query = self._where_calc(args)
            self._apply_ir_rules(where_query, 'read')
            from_clause, where_clause, where_clause_params = where_query.get_sql()
            where_str = where_clause and (" WHERE %s AND " % where_clause) or ' WHERE '

            # search on the name of the contacts and of its company
            search_name = name
            if operator in ('ilike', 'like'):
                search_name = '%%%s%%' % name
            if operator in ('=ilike', '=like'):
                operator = operator[1:]

            unaccent = get_unaccent_wrapper(self.env.cr)

            query = """SELECT id
                         FROM res_partner
                      {where} ({poldocument} {operator} {percent})
                     ORDER BY {display_name} {operator} {percent} desc,
                              {display_name}
                    """.format(where=where_str,
                               operator=operator,
                               poldocument=unaccent('poldocument'),
                               display_name=unaccent('display_name'),
                               percent=unaccent('%s'),)

            where_clause_params += [search_name]*2
            if limit:
                query += ' limit %s'
                where_clause_params.append(limit)
            self.env.cr.execute(query, where_clause_params)
            partner_ids = [row[0] for row in self.env.cr.fetchall()]
            if partner_ids:
                result += self.browse(partner_ids).name_get()
        return result

    #TMP_FIX VAT Validation
    @api.constrains("vat")
    def check_vat(self):
        return

    #TODO: Review better VAT & DocumentNumber integration
    @api.onchange('document_number')
    def onchange_poldocument(self):
        for partner in self:
            if partner.document_number and partner.document_type == 'D':
                partner.vat = 'ES' + partner.poldocument
