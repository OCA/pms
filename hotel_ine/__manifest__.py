# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2019 Jose Luis Algara Toledo <osotranquilo@gmail.com>
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
    'name': 'Hotel Ine',
    'description': """
        Create de INE Report""",
    'version': '1.0.0',
    'license': 'AGPL-3',
    'summary': "Export hotel data for INE report",
    'author': "Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>",
    'website': 'www.aldahotels.com',
    'depends': ['hotel', 'hotel_l10n_es'],
    'category': 'hotel/ine',
    'data': [
            'wizard/inewizard.xml',
            'views/inherited_hotel_room_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
