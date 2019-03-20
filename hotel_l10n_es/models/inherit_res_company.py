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
import base64
from odoo import models, fields
from odoo import modules


def get_default_img():
    with open(modules.get_module_resource('hotel_l10n_es', 'static/src/img',
                                          'logo_bn.png'),
              'rb') as f:
        return base64.b64encode(f.read())


class Inherit_res_company(models.Model):
    _inherit = 'res.company'

    property_name = fields.Char('Property name',
                                help='Name of the Hotel/Property.')
    ine_tourism = fields.Char('Tourism number',
                              help='Registration number in the Ministry of \
                                            Tourism. Used for INE statistics.')
    ine_rooms = fields.Integer('Rooms Available', default=0,
                               help='Used for INE statistics.')
    ine_seats = fields.Integer('Beds available', default=0,
                               help='Used for INE statistics.')
    ine_permanent_staff = fields.Integer('Permanent Staff', default=0,
                                         help='Used for INE statistics.')
    ine_eventual_staff = fields.Integer('Eventual Staff', default=0,
                                        help='Used for INE statistics.')
    police_number = fields.Char('Police number', size=10,
                                help='Used to generate the name of the file that \
                                will be given to the police. 10 Caracters')
    ine_category_id = fields.Many2one('tourism.category',
                                      help='Hotel category in the Ministry of \
                                            Tourism. Used for INE statistics.')
    checkin_img = fields.Binary(string="Image in checkin",
                                default=get_default_img())
