# Copyright (c) 2021 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "PMS - CRM",
    "summary": "Link leads to properties",
    "version": "19.0.1.0.0",
    "development_status": "Beta",
    "category": "Generic Modules/Property Management System",
    "website": "https://github.com/OCA/pms",
    "author": "Gray Matter Logic, Odoo Community Association (OCA)",
    "maintainers": ["max3903"],
    "license": "AGPL-3",
    "depends": ["crm", "pms_base"],
    "demo": [
        "demo/crm_lead.xml",
    ],
    "data": ["views/crm_lead.xml", "views/pms_property.xml"],
}
