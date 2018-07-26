# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Hotel Calendar',
    'version': '11.0.2.0',
    'author': "Alexandre Díaz <dev@redneboa.es>",
    'website': 'https://www.eiqui.com',
    'category': 'hotel/calendar',
    'summary': "Hotel Calendar",
    'description': "Hotel Calendar",
    'depends': [
        'bus',
        'web',
        'calendar',
        'hotel',
        'web_widget_color',
    ],
    'external_dependencies': {
        'python': []
    },
    'data': [
        'views/general.xml',
        'views/actions.xml',
        'views/res_config_views.xml',
        'views/inherited_res_users_views.xml',
        'views/inherited_hotel_virtual_room_views.xml',
        'views/inherited_hotel_room_views.xml',
        'views/virtual_room_pricelist_cached_views.xml',
        'data/views.xml',
        'data/menus.xml',
        'data/records.xml',
        'security/ir.model.access.csv',
        'wizard/wizard_reservation.xml'
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'test': [
    ],

    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
