# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2018-2019 Jose Luis Algara Toledo <osotranquilo@gmail.com>
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
    'name': 'Hotel Door Codes',
    'version': '2.1',
    'author': "Jose Luis Algara Toledo <osotranquilo@gmail.com>",
    'website': 'https://www.aldahotels.com',
    'category': 'hotel code',
    'summary': "Generate Hotel door codes, in Pseudo random system",
    'description': "Hotel Door Codes",
    'depends': [
        'hotel', 'hotel_l10n_es'
    ],
    'data': [
        'wizard/door_code.xml',
        'data/menus.xml',
        'views/inherit_res_company.xml',
        'views/inherit_hotel_reservation.xml',
        'views/inherit_report_viajero.xml',
    ],
    'qweb': [],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',
}
