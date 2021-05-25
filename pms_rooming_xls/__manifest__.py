# Copyright 2009-2020 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Rooming xlsx Management",
    "author": "Commit [Sun], Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/pms",
    "category": "Generic Modules/Property Management System",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "report_xlsx_helper",
        "pms",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/import_rooming_xlsx.xml",
        "views/pms_folio.xml",
    ],
    "external_dependencies": {"python": ["xlrd"]},
    "installable": True,
}
