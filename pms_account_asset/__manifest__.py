# Copyright 2019 Darío Lodeiros, Alexandre Díaz, Jose Luis Algara, Pablo Quesada
# Copyright (c) 2021 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "PMS - Asset Management",
    "summary": "Manage the assets related to your properties",
    "version": "19.0.1.0.1",
    "development_status": "Beta",
    "category": "Generic Modules/Property Management System",
    "website": "https://github.com/OCA/pms",
    "author": "Gray Matter Logic, Odoo Community Association (OCA)",
    "maintainers": ["eantones"],
    "license": "AGPL-3",
    "depends": [
        "account_asset_management",
        "pms_account",
    ],
    "demo": [
        "demo/account_journal_demo.xml",
        "demo/account_account_demo.xml",
        "demo/account_asset_profile_demo.xml",
        "demo/account_asset.xml",
    ],
    "data": [
        "views/account_asset.xml",
        "views/pms_property.xml",
        "views/menu.xml",
    ],
}
