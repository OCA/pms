# Copyright (C) 2022 Open Source Integrators (https://www.opensourceintegrators.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "PMS - Sale - Stock",
    "summary": "Manage checkouts",
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "category": "Generic Modules/Property Management System",
    "website": "https://github.com/OCA/pms",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "maintainers": ["max3903"],
    "license": "AGPL-3",
    "depends": ["pms_sale", "pms_stock", "stock_location_content_template"],
    "data": [
        "views/pms_reservation.xml",
        "views/stock_location_content_check.xml",
    ],
}
