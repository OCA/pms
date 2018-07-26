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
    'name': 'Hotel WuBook Prototype',
    'version': '1.0',
    'author': "Alexandre Díaz (Aloxa Solucións S.L.) <alex@aloxa.eu>",
    'website': 'https://www.eiqui.com',
    'category': 'eiqui/hotel',
    'summary': "Hotel WuBook",
    'description': "Hotel WuBook Prototype",
    'depends': [
        'hotel',
    ],
    'external_dependencies': {
        'python': ['xmlrpc']
    },
    'data': [
        'data/cron_jobs.xml',
        'wizard/wubook_installer.xml',
        'wizard/wubook_import_plan_prices.xml',
        'wizard/wubook_import_plan_restrictions.xml',
        'wizard/wubook_import_availability.xml',
        'views/general.xml',
        'views/res_config_views.xml',
        'views/inherited_hotel_reservation_views.xml',
        'views/inherited_hotel_virtual_room_views.xml',
        'views/inherited_hotel_virtual_room_availability_views.xml',
        'views/inherited_hotel_folio_views.xml',
        'views/inherited_product_pricelist_views.xml',
        'views/inherited_product_pricelist_item_views.xml',
        'views/inherited_reservation_restriction_views.xml',
        'views/inherited_reservation_restriction_item_views.xml',
        'views/inherited_res_partner_views.xml',
        'views/wubook_channel_info_views.xml',
        'views/wubook_issue_views.xml',
        'data/menus.xml',
        'data/sequences.xml',
        'security/ir.model.access.csv',
        'security/wubook_security.xml',
        # 'views/res_config.xml'
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',
}
