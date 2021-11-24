# Copyright 2019 Darío Lodeiros, Alexandre Díaz, Jose Luis Algara, Pablo Quesada
# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Property Management System",
    "summary": "Manage contracts related to your properties",
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "category": "Generic Modules/Property Management System",
    "website": "https://github.com/OCA/pms",
    "author": "Commit [Sun], Open Source Integrators, Odoo Community Association (OCA)",
    "maintainers": ["eantones"],
    "license": "AGPL-3",
    "depends": [
        "contract",
        "pms_account",
    ],
    "data": [
        "views/pms_service.xml",
        "views/contract_contract.xml",
        "views/pms_property.xml",
        "views/menu.xml",
    ],
}
