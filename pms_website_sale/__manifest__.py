# Copyright (c) 2021 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "PMS - Website Sale",
    "summary": "Allow online booking of your properties",
    "version": "19.0.1.0.0",
    "development_status": "Beta",
    "category": "Generic Modules/Property Management System",
    "website": "https://github.com/OCA/pms",
    "author": "Gray Matter Logic, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["pms_website", "pms_sale", "website_sale"],
    "demo": [
        "demo/pms_property_reservation.xml",
        "demo/pms_reservation.xml",
    ],
    "data": [
        "data/website_menu.xml",
        "security/ir.model.access.csv",
        "security/pms_website_sale.xml",
        "views/templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "pms_website_sale/static/src/js/pms_property.js",
            "pms_website_sale/static/src/js/pms_property_booking.js",
        ],
        "web.assets_tests": [
            "pms_website_sale/static/tests/tours/pms_website_sale_tour.test.js",
        ],
    },
    "maintainers": ["max3903"],
}
