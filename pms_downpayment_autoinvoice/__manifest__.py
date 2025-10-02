{
    "name": "PMS Downpayment Auto-Invoicing",
    "summary": (
        "Automated downpayment invoicing for PMS by company schedule "
        "(daily/weekly/monthly/quarterly)."
    ),
    "version": "16.0.1.0.0",
    "category": "Accounting/Hotel PMS",
    "license": "AGPL-3",
    "author": ("Odoo Community Association (OCA), " "Roomdoo"),
    "website": "https://github.com/OCA/pms",
    "depends": [
        "account",
        "pms",
    ],
    "data": [
        "views/res_company_views.xml",
        "data/ir_cron.xml",
    ],
    "installable": True,
    "application": False,
}
