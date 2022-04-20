# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "PMS - Website",
    "summary": "Publish properties on the website",
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "category": "Generic Modules/Property Management System",
    "website": "https://github.com/OCA/pms",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["pms_base", "website"],
    "data": [
        "security/ir.model.access.csv",
        "data/rule.xml",
        "views/pms_property_template.xml",
        "views/pms_property.xml",
        "views/pms_amenity_views.xml",
        "views/pms_website_category_views.xml",
    ],
}
