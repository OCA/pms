# Copyright 2018 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Hotel RoomMatik',
    'description': """
        Integration of Hootel with the RoomMatik kiosk""",
    'summary': """
        The integration of Hootel with the RoomMatik kiosk.
        A series of requests/responses that provide the basic
        information needed by the kiosk.""",
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>',
    'website': 'https://www.aldahotels.com',
    'category': 'Generic Modules/Hotel Management',
    'depends': [
        'hotel',
        'partner_contact_gender',
        'partner_contact_birthdate',
        'base_iso3166',
        'base_location',
    ],
    'data': [
        'data/res_users_data.xml'
    ],
    'demo': [
    ],
}
