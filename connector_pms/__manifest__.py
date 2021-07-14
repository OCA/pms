# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "PMS Connector",
    "summary": "Channel PMS connector Base",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "development_status": "Alpha",
    "category": "Connector",
    "website": "https://github.com/OCA/pms",
    "author": "Eric Antones <eantones@nuobit.com>,Odoo Community Association (OCA)",
    "depends": [
        "connector",
        "pms",
    ],
    "data": [
        "data/queue_data.xml",
        "security/ir.model.access.csv",
        "views/channel_menus.xml",
        "views/channel_backend_views.xml",
        "views/channel_backend_type_views.xml",
        "views/pms_property_views.xml",
        "views/pms_room_type_views.xml",
        "views/pms_room_type_class_views.xml",
        "views/pms_board_service_views.xml",
        "views/pms_folio_views.xml",
        "views/pms_reservation_views.xml",
        "views/product_pricelist_views.xml",
        "views/product_pricelist_item_views.xml",
        "views/pms_availability_plan_views.xml",
        "views/pms_availability_plan_rule_views.xml",
    ],
}
