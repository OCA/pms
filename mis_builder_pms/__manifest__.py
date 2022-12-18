# Copyright 2022 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "MIS Builder with PMS Properties",
    "summary": "Add property in mis builder",
    "version": "14.0.1.0.0",
    "development_status": "Beta",
    "category": "Reporting",
    "website": "https://github.com/OCA/pms",
    "author": "Comunitea, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["mis_builder", "pms"],
    "data": [
        "views/mis_builder_view.xml",
    ],
    "auto_install": True,
}
