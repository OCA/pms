# © 2023 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Property in Account Move Budget",
    "summary": "Add Property Field in Account Move Budget",
    "version": "16.0.1.0.0",
    "category": "Custom",
    "website": "https://github.com/OCA/pms",
    "author": "Comunitea, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account_move_budget",
        "pms",
    ],
    "data": [
        "views/account_move_budget_line_view.xml",
    ],
}
