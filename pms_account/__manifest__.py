# Copyright 2019 Darío Lodeiros, Alexandre Díaz, Jose Luis Algara, Pablo Quesada
# Copyright (c) 2021 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "PMS - Accounting",
    "summary": "Manage the accounting aspects of your properties",
    "version": "19.0.1.0.0",
    "development_status": "Beta",
    "category": "Generic Modules/Property Management System",
    "website": "https://github.com/OCA/pms",
    "author": "Gray Matter Logic, Odoo Community Association (OCA)",
    "maintainers": ["max3903"],
    "license": "AGPL-3",
    "depends": [
        "account",
        "analytic",
        "pms_base",
    ],
    "demo": [
        "demo/account_analytic_account.xml",
    ],
    "data": [
        "data/analytic_plan.xml",
        "views/account_analytic_account.xml",
        "views/account_move.xml",
        "views/pms_property.xml",
    ],
}
