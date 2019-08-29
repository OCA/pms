# -*- coding: utf-8 -*-
# Copyright 2018 Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Hotel Management',
    'version': '11.0.2.0.0',
    'author': 'Odoo Community Association (OCA),\
    Darío Lodeiros,\
    Jose Luis Algara,\
    Alexandre Díaz,\
    Q. Barriuso,',
    'category': 'Generic Modules/Hotel Management',
    'website': 'https://github.com/hootel/hootel',
    'depends': [
        'base',
        'sale_stock',
        'account_payment_return',
        'partner_firstname',
        'account_cancel'
    ],
    'license': "AGPL-3",
    'demo': ['data/hotel_demo.xml'],
    'data': [
        'security/hotel_security.xml',
        'security/ir.model.access.csv',
        'wizard/massive_changes.xml',
        'wizard/split_reservation.xml',
        'wizard/service_on_day.xml',
        'views/res_config.xml',
        'data/menus.xml',
        'views/inherited_account_payment_views.xml',
        'views/inherited_account_invoice_views.xml',
        'wizard/massive_price_reservation_days.xml',
        'wizard/folio_make_invoice_advance_views.xml',
        'data/hotel_sequence.xml',
        'views/hotel_floor_views.xml',
        'views/hotel_folio_views.xml',
        'views/inherited_res_partner_views.xml',
        'views/hotel_room_type_views.xml',
        'views/hotel_room_views.xml',
        'views/hotel_shared_room_views.xml',
        'views/hotel_room_type_class_views.xml',
        'views/general.xml',
        'views/inherited_product_template_views.xml',
        'views/inherited_product_pricelist_views.xml',
        'views/hotel_room_amenities_type_views.xml',
        'views/hotel_room_amenities_views.xml',
        'views/hotel_room_type_restriction_views.xml',
        'views/hotel_room_type_restriction_item_views.xml',
        'views/hotel_reservation_views.xml',
        'views/hotel_room_closure_reason_views.xml',
        'views/hotel_service_views.xml',
        'views/hotel_service_line_views.xml',
        'views/hotel_board_service_views.xml',
        'views/hotel_checkin_partner_views.xml',
        'views/hotel_board_service_room_type_views.xml',
        'views/hotel_cancelation_rule_views.xml',
        'data/cron_jobs.xml',
        'data/records.xml',
        'data/email_template_cancel.xml',
        'data/email_template_reserv.xml',
        'data/email_template_exit.xml',
        'wizard/wizard_reservation.xml',
        'report/hotel_folio_templates.xml',
        'report/hotel_folio.xml'
    ],
    'installable': True
}
