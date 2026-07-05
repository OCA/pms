# Copyright (c) 2021 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "PMS - Website",
    "summary": "Publish properties on the website",
    "version": "19.0.1.0.0",
    "development_status": "Beta",
    "category": "Generic Modules/Property Management System",
    "website": "https://github.com/OCA/pms",
    "author": "Gray Matter Logic, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["pms_base", "website"],
    "demo": [
        "demo/pms_website_category.xml",
        "demo/pms_property.xml",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/rule.xml",
        "views/pms_property_template.xml",
        "views/pms_property.xml",
        "views/pms_amenity_views.xml",
        "views/pms_website_category_views.xml",
    ],
}
