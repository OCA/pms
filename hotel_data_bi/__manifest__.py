# -*- coding: utf-8 -*-
# Copyright 2018-2019 Jose Luis Algara Toledo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Hotel Data Bi',
    'description': """
        Export hotel data for business intelligence

    To use this module you need to:

    Create a user and give the 'Hotel Management/Export data BI' permission.
        """,
    'summary': "Export hotel data for business intelligence",
    'version': '2.1',
    'license': 'AGPL-3',
    'author': "Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>",
    'website': 'www.aldahotels.com',
    'depends': ['hotel', 'hotel_l10n_es', 'hotel_channel_connector'],
    'category': 'hotel/revenue',
    'data': [
        'views/budget.xml',
        'views/inherit_res_company.xml',
        'security/data_bi.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
