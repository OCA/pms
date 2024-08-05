# Copyright 2024 OsoTranquilo - José Luis Algara
# Copyright 2024 Irlui Ramírez
# From Consultores Hoteleros Integrales (ALDA Hotels) - 2024
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "PMS Property Opening",
    "version": "14.0.1.0.0",
    "category": "PMS",
    "summary": """ Information regarding the opening of property """,
    "author": "Irlui Ramirez,José Luis Algara,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/pms",
    "depends": ["base", "pms"],
    "data": [
        "views/pms_property_view.xml",
    ],
    "application": True,
    "installable": True,
    "auto_install": True,
    "license": "AGPL-3",
}
