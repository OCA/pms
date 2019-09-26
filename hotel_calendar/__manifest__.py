# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Roomdoo Calendar',
    'summary': 'A calendar view for user friendly handling your roomdoo property.',
    'version': '11.0.2.0',
    'development_status': 'Beta',
    'category': 'Generic Modules/Hotel Management',
    'website': 'https://github.com/hootel/hootel',
    'author': 'Alexandre Díaz <dev@redneboa.es>',
    'license': "AGPL-3",
    'application': False,
    'installable': True,
    'depends': [
        'bus',
        'web',
        'calendar',
        'hotel',
        'web_widget_color',
    ],
    # 'external_dependencies': {
    #     'python': []
    # },
    'data': [
        'views/general.xml',
        'views/actions.xml',
        'views/inherited_hotel_property_views.xml',
        'views/inherited_res_company_views.xml',
        'views/inherited_res_users_views.xml',
        'views/hotel_reservation_views.xml',
        'views/hotel_calendar_management_views.xml',
        'views/hotel_calendar_views.xml',
        'data/menus.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
        'static/src/xml/hotel_calendar_management_view.xml',
        'static/src/xml/hotel_calendar_templates.xml',
        'static/src/xml/hotel_calendar_view.xml',
    ],
}
