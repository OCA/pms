# Copyright (c) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "PMS - Purchase",
    "summary": "Select a PMS property on the PO line.",
    "version": "14.0.1.0.0",
    "category": "purchase",
    "website": "https://github.com/OCA/pms",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "maintainers": ["max3903"],
    "license": "AGPL-3",
    "depends": ["pms_account", "purchase_stock", "pms_stock", "stock_putaway_method"],
    "data": [
        "views/purchase_order.xml",
        "views/pms_property.xml",
        "views/stock_putaway_views.xml",
    ],
    "development_status": "Beta",
}
