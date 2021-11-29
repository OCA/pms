# Copyright 2019 Darío Lodeiros, Alexandre Díaz, Jose Luis Algara, Pablo Quesada
# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "PMS - Sale",
    "summary": "Manage reservations",
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "category": "Generic Modules/Property Management System",
    "website": "https://github.com/OCA/pms",
    "author": "Commit [Sun], Open Source Integrators, Odoo Community Association (OCA)",
    "maintainers": ["eantones"],
    "license": "AGPL-3",
    "depends": ["pms_account", "sale", "web_timeline", "calendar"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "data/product_data.xml",
        "data/pms_stage.xml",
        "views/assets.xml",
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
    "qweb": ["static/src/xml/timeline.xml"],
}
