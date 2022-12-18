# Copyright 2022 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Assets Management PMS",
    "summary": "Add property in assets configuration",
    "version": "14.0.1.0.0",
    "development_status": "Beta",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/pms",
    "author": "Comunitea, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["account_asset_management", "pms"],
    "data": [
        "views/account_asset_view.xml",
    ],
    "auto_install": True,
}
