# Copyright 2020-21 Jose Luis Algara (Alda Hotels <https://www.aldahotels.es>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "OCR Regula",
    "version": "14.0.1.0.1",
    "author": "Commit [Sun], Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": True,
    "category": "Generic Modules/Property Management System",
    "website": "https://github.com/OCA/pms",
    "depends": [
        "pms_api_rest",
    ],
    "external_dependencies": {
        "python": ["regula.documentreader.webclient", "marshmallow"],
    },
    "data": ["views/pms_property_views.xml", "data/pms_ocr_regula_data.xml"],
    "installable": True,
}
