{
    'name': 'Hotel Node Helper',
    'summary': """Provides helper functions to the hotel node master module""",
    'version': '0.1.0',
    'author': 'Pablo Q. Barriuso, \
               Darío Lodeiros, \
               Alexandre Díaz, \
               Odoo Community Association (OCA)',
    'category': 'Generic Modules/Hotel Management',
    'depends': [
        'hotel'
    ],
    'license': "AGPL-3",
    'data': [
        'security/hotel_node_security.xml',
        'security/ir.model.access.csv'
    ],
    'demo': [],
    'auto_install': False,
    'installable': True
}
