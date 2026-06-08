# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "PMS - Purchase",
    "summary": "Select a PMS property on the PO line.",
    "version": "19.0.1.0.0",
    "category": "purchase",
    "website": "https://github.com/OCA/pms",
    "author": "Gray Matter Logic, Odoo Community Association (OCA)",
    "maintainers": ["max3903"],
    "license": "AGPL-3",
    "depends": ["pms_account", "purchase_stock", "pms_stock"],
    "demo": [
        "demo/purchase_order.xml",
    ],
    "data": [
        "views/purchase_order.xml",
        "views/pms_property.xml",
        "views/stock_putaway_views.xml",
    ],
    "development_status": "Beta",
}
