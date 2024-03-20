# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

{
    "name": "PMS Website Sale",
    "summary": """
        Book and pay for hotel reservations online.""",
    "version": "14.0.1.0.0",
    "category": "E-commerce",
    "website": "https://github.com/OCA/pms",
    "author": "Coop IT Easy SC, Odoo Community Association (OCA)",
    "maintainers": ["carmenbianca", "robinkeunen", "remytms"],
    "license": "AGPL-3",
    "application": False,
    "depends": [
        "payment",
        "pms",
        # todo remove website_sale dependency
        #  We're only using a _portion_ of website_sale for our functionality.
        #  payments can be dealt with sepraratly, other minor things depend on it
        "website_sale",
        "website_legal_page",
    ],
    "excludes": [],
    "data": [
        "security/ir.model.access.csv",
        "security/pms_website_sale.xml",
        "data/data.xml",
        "views/pms_room_type_views.xml",
        "templates/pms_assets_templates.xml",
        "templates/pms_common_templates.xml",
        "templates/pms_rooms_list_templates.xml",
        "templates/pms_room_type_templates.xml",
        "templates/pms_review_booking_templates.xml",
        "templates/pms_extra_info_templates.xml",
        "templates/pms_address_templates.xml",
        "templates/pms_booking_payment_templates.xml",
    ],
    "demo": [],
    "qweb": [],
}
