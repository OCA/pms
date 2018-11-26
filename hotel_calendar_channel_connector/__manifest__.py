# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Hotel Calendar Channel Connector',
    'version': '11.0.2.0',
    'author': "Alexandre Díaz <dev@redneboa.es>",
    'website': 'https://github.com/hootel/hootel',
    'category': 'hotel/addon',
    'summary': "Hotel Calendar Channel Connector",
    'description': "Unify 'hotel_calendar' and 'hotel_channel_connector'",
    'depends': [
        'hotel_calendar',
        'hotel_channel_connector',
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

    'installable': True,
    'auto_install': True,
    'application': False,
    'license': 'AGPL-3',
}
