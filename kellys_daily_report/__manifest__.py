# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2018 Jose Luis Algara Toledo <osotranquilo@gmail.com>
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
    'name': 'Hotel Kellys Daily Report',
    'version': '2.1',
    'author': "Jose Luis Algara Toledo <osotranquilo@gmail.com>",
    'website': 'https://www.aldahotels.com',
    'category': 'hotel report kellys',
    'summary': "Export daily report in PDF format",
    'description': "Kellys Daily Report",
    'depends': [
        'hotel',
    ],
    'data': [
        'data/report_kellys_paperformat.xml',
        'views/kellysnames.xml',
        'wizard/kellys_daily_rooms.xml',
        'wizard/kellys_daily_pdf.xml',
        'data/menus.xml',
        'report/report_kellys.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [],
    'test': [
    ],
    'css': ['static/src/css/kellys_daily_report.css'],

    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',
}
