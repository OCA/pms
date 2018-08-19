# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <dev@redneboa.es>
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
    'name': 'Hotel Calendar WuBook',
    'version': '1.0',
    'author': "Alexandre Díaz (Aloxa Solucións S.L.) <alex@aloxa.eu>",
    'website': 'https://www.eiqui.com',
    'category': 'eiqui/hotel',
    'summary': "Hotel Calendar",
    'description': "Hotel Calendar WuBook",
    'depends': [
        'hotel_calendar',
        'hotel_wubook_proto',
    ],
    'external_dependencies': {
        'python': []
    },
    'data': [
        'views/hotel_reservation.xml',
        'views/general.xml',
        'views/actions.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'test': [
    ],

    'installable': False,
    'auto_install': True,
    'application': False,
    'license': 'AGPL-3',
}
