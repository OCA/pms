# Copyright (C) 2024 Irlui Ramírez <iramirez.spain@gmail.com>
# Copyright (C) 2024 Oso Tranquilo <informatica@gmail.com>
# Copyright (C) 2024 Consultores Hoteleros Integrales <www.aldahotels.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "PMS Helpdesk Management",
    "version": "14.0.1.0.0",
    "summary": """ Add the option to select property in the tickets. """,
    "author": "Irlui Ramirez, "
    "Consultores Hoteleros Integrales, "
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/pms",
    "category": "After-Sales/Pms",
    "depends": ["base", "web", "helpdesk_mgmt", "pms", "portal"],
    "data": [
        "views/helpdesk_ticket_views.xml",
        "views/helpdesk_ticket_templates.xml",
        "securitty/helpdesk_security_pms.xml",
    ],
    "demo": ["demo/helpdesk_demo.xml"],
    "assets": {
        "web.assets_frontend": [
            "pms_helpdesk_mgmt/static/src/js/hotel_on_company.js",
        ],
    },
    "application": True,
    "installable": True,
    "auto_install": True,
    "license": "AGPL-3",
}
