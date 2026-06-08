# Copyright 2019 Darío Lodeiros, Alexandre Díaz, Jose Luis Algara, Pablo Quesada
# Copyright (c) 2021 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "PMS - Sale",
    "summary": "Manage reservations",
    "version": "19.0.1.0.0",
    "development_status": "Beta",
    "category": "Generic Modules/Property Management System",
    "website": "https://github.com/OCA/pms",
    "author": "Gray Matter Logic, Odoo Community Association (OCA)",
    "maintainers": ["max3903"],
    "license": "AGPL-3",
    "depends": ["pms_account", "sale", "web_timeline", "calendar"],
    "demo": [
        "demo/res_partner.xml",
        "demo/pms_property.xml",
        "demo/pms_property_reservation.xml",
        "demo/pms_reservation.xml",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "data/product_data.xml",
        "data/pms_stage.xml",
        "views/product_views.xml",
        "views/pms_property_reservation.xml",
        "views/pms_mail_views.xml",
        "views/pms_property.xml",
        "views/pms_reservation_guest_views.xml",
        "views/pms_reservation_views.xml",
        "wizards/pms_configurator_views.xml",
        "views/sale_order_views.xml",
        "views/pms_team_views.xml",
        "views/menu.xml",
        "views/account_move.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "pms_sale/static/src/js/pms_configurator_controller.esm.js",
            "pms_sale/static/src/js/pms_sale_product_field.esm.js",
            "pms_sale/static/src/js/timeline.esm.js",
        ],
    },
}
