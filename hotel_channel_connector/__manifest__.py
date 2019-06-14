# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Hotel Channel Connector',
    'version': '1.0',
    'author': "Alexandre Díaz <dev@redneboa.es>",
    'website': 'https://github.com/hootel/hootel',
    'category': 'hotel/connector',
    'summary': "Hotel Channel Connector Base",
    'description': "Hotel Channel Connector Base",
    'depends': [
        'connector',
        'web_notify',
        'hotel',
    ],
    'external_dependencies': {
        'python': ['xmlrpc']
    },
    'data': [
        'views/hotel_channel_connector_issue_views.xml',
        'views/hotel_room_type_availability_views.xml',
        'views/inherited_hotel_reservation_views.xml',
        'views/inherited_hotel_room_type_views.xml',
        'views/inherited_hotel_folio_views.xml',
        'views/inherited_product_pricelist_views.xml',
        'views/inherited_product_pricelist_item_views.xml',
        'views/inherited_hotel_room_type_restriction_views.xml',
        'views/inherited_hotel_room_type_restriction_item_views.xml',
        'views/channel_hotel_reservation_views.xml',
        'views/channel_hotel_room_type_views.xml',
        'views/channel_hotel_room_type_availability_views.xml',
        'views/channel_hotel_room_type_restriction_views.xml',
        'views/channel_hotel_room_type_restriction_item_views.xml',
        'views/channel_product_pricelist_views.xml',
        'views/channel_product_pricelist_item_views.xml',
        'views/channel_connector_backend_views.xml',
        'views/channel_ota_info_views.xml',
        'wizard/inherited_massive_changes.xml',
        'data/menus.xml',
        'data/cron_jobs.xml',
        'data/email_availability_watchdog.xml',
        'security/ir.model.access.csv',
        #'security/wubook_security.xml',
        # 'views/res_config.xml'
    ],
    'test': [
    ],
    'installable': True,
    'license': 'AGPL-3',
}
