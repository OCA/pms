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
        'views/inherited_res_users_views.xml',
        # 'views/inherited_hotel_room_type_views.xml',
        # 'views/inherited_hotel_room_views.xml',
        'views/hotel_reservation_views.xml',
        'views/hotel_calendar_management_views.xml',
        'views/hotel_calendar_views.xml',
        'data/menus.xml',
        'views/res_config.xml',
        'data/ir_config_parameter.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'test': [
    ],

    'installable': True,
    'license': 'AGPL-3',
}
