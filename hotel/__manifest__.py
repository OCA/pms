# Copyright 2019 Darío Lodeiros, Alexandre Díaz, Jose Luis Algara, Pablo Quesada
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'roomdoo',
    'summary': "A property management system focused on medium-sized hotels",
    'version': '11.0.2.0.0',
    'development_status': 'Beta',
    'category': 'Generic Modules/Hotel Management',
    'website': 'https://github.com/hootel/hootel',
    'author': 'Darío Lodeiros, '
              'Alexandre Díaz, '
              'Jose Luis Algara, '
              'Pablo Quesada ',
    'license': "AGPL-3",
    'application': False,
    'installable': True,
    'depends': [
        'base',
        'sale_stock',
        'account_payment_return',
        'partner_firstname',
        'account_cancel'
    ],
    'data': [
        'data/cron_jobs.xml',
        'data/email_template_cancel.xml',
        'data/email_template_reserv.xml',
        'data/email_template_exit.xml',
        'data/menus.xml',
        'data/hotel_data.xml',
        'data/hotel_sequence.xml',
        'report/hotel_folio.xml'
        'report/hotel_folio_templates.xml',
        'security/hotel_security.xml',
        'security/ir.model.access.csv',

        'views/general.xml',
        'views/hotel_amenity_views.xml',
        'views/hotel_amenity_type_views.xml',
        'views/hotel_board_service_views.xml',
        'views/hotel_board_service_room_type_views.xml',
        'views/hotel_cancelation_rule_views.xml',
        'views/hotel_checkin_partner_views.xml',
        'views/hotel_floor_views.xml',
        'views/hotel_folio_views.xml',
        'views/hotel_property_views.xml',
        'views/hotel_reservation_views.xml',
        'views/hotel_room_views.xml',
        'views/hotel_room_closure_reason_views.xml',
        'views/inherited_account_payment_views.xml',
        'views/inherited_account_invoice_views.xml',
        'views/inherited_res_users_views.xml',
        'views/hotel_room_type_views.xml',
        'views/hotel_room_type_class_views.xml',
        'views/hotel_room_type_restriction_views.xml',
        'views/hotel_room_type_restriction_item_views.xml',
        'views/hotel_service_views.xml',
        'views/hotel_service_line_views.xml',
        'views/hotel_shared_room_views.xml',
        'views/inherited_res_partner_views.xml',
        'views/inherited_product_pricelist_views.xml',
        'views/inherited_product_template_views.xml',
        'views/inherited_webclient_templates.xml',
        'wizard/folio_make_invoice_advance_views.xml',
        'wizard/massive_changes.xml',
        'wizard/massive_price_reservation_days.xml',
        'wizard/service_on_day.xml',
        'wizard/split_reservation.xml',
        'wizard/wizard_reservation.xml',
    ],
    'demo': [
        'demo/hotel_demo.xml'
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
}
