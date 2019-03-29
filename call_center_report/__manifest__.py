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

{
    'name': 'Call Center Report',
    'version': '1.0',
    'author': "Dario Lodeiros",
    'website': 'https://www.eiqui.com',
    'category': 'reports',
    'summary': "Export services and reservation report in xls format",
    'description': "Call Center Report",
    'depends': [
        'hotel',
    ],
    'external_dependencies': {
        'python': ['xlsxwriter']
    },
    'data': [
        'wizard/call_center_report.xml',
        'data/menus.xml',
    ],
    'qweb': [],
    'test': [
    ],

    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',
}
