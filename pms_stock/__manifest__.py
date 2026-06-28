# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "PMS - Stock",
    "summary": "Manage the content of a property.",
    "version": "19.0.1.0.0",
    "development_status": "Beta",
    "category": "Generic Modules/Property Management System",
    "website": "https://github.com/OCA/pms",
    "author": "Gray Matter Logic, Odoo Community Association (OCA)",
    "maintainers": ["max3903"],
    "license": "AGPL-3",
    "depends": ["pms_base", "stock"],
    "demo": [
        "demo/stock_location.xml",
        "demo/pms_property.xml",
    ],
    "data": ["views/pms_property.xml"],
}
