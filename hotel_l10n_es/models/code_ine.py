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

from openerp import models, fields, api


class CodeIne(models.Model):
    _name = 'code.ine'

    name = fields.Char('Place', required=True)
    code = fields.Char('Code', required=True)

    @api.multi
    def name_get(self):
        data = []
        for record in self:
            subcode = record.code
            if len(record.code) > 3:
                subcode = 'ESP'
            display_value = record.name + " (" + subcode + ")"
            data.append((record.id, display_value))
        return data
