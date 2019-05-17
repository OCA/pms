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


{
    'name': 'Hotel l10n_es',
    'version': '9.0.0.3',
    'author': "Jose Luis Algara",
    'website': "http://www.aldahotels.com",
    'category': 'Hotel',
    'summary': "",
    'description': "",
    'depends': [
        'hotel',
        'partner_contact_gender',
        'partner_contact_birthdate',
        'partner_firstname',
        'partner_vat_unique',
    ],
    'data': [
        'data/code.ine.csv',
        'data/tourism.category.csv',
        'data/report_viajero_paperformat.xml',
        'report/report_parte_viajero.xml',
        'views/report_viajero.xml',
        'wizard/police_wizard.xml',
        'views/category_tourism.xml',
        'views/code_ine.xml',
        'views/inherit_res_company.xml',
        'views/inherit_hotel_checkin_partner_views.xml',
        'security/ir.model.access.csv',
        'views/inherit_res_partner.xml',
        'views/inherited_hotel_reservation_views.xml',
        'views/report_viajero_document.xml',
        'views/report_viajero_head.xml',
        'views/report_viajero_data.xml',
        'views/report_viajero.xml',
        'views/hotel_l10n_es_hotel_name.xml'
    ],
    'test': [
    ],
    'css': ['static/src/css/hotel_l10n_es.css'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',
}
