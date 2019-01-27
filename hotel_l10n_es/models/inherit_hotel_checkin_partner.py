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


class HotelCheckinPartner(models.Model):
    _inherit = 'hotel.checkin.partner'

    document_type = fields.Selection(related='partner_id.document_type')
    document_number = fields.Char(related='partner_id.document_number')
    document_expedition_date = fields.Date(related='partner_id.document_expedition_date')

    code_ine_id = fields.Many2one(related="partner_id.code_ine_id")

    #TMP_FIX VAT Validation
    @api.constrains("vat")
    def check_vat(self):
        return
