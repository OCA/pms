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
    "author": "Coop IT Easy SC",
    "maintainers": [
        "carmenbianca",
        "robinkeunen",
    ],
    "license": "AGPL-3",
    "application": False,
    "depends": [
        "pms",
        # We're only using a _portion_ of website_sale for our functionality.
        # Specifically, we're using the online payment integration facilitated
        # by website_sale. We are not using the /shop interface for buying
        # products, because room reservations are not products.
        #
        # In a better world, the online payment stuff would live in a module
        # separate from website_sale, but that is not the world in which we
        # live.
        "website_sale",
    ],
    "excludes": [],
    "data": [
        "security/ir.model.access.csv",
        "security/pms_website_sale.xml",
        "data/data.xml",
        "views/templates.xml",
        "views/pms_room_type_views.xml",
    ],
    "demo": [],
    "qweb": [],
}
