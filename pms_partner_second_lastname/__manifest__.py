{
    "name": "PMS partner second lastname",
    "version": "16.0.2.1.0",
    "summary": "Add lastname2 in pms models",
    "development_status": "Beta",
    "category": "Generic Modules/Property Management System",
    "website": "https://github.com/OCA/pms",
    "author": "Commit [Sun], Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "pms",
        "partner_second_lastname",
    ],
    "data": [
        "views/pms_checkin_partner.xml",
        "views/res_partner.xml",
        "views/traveller_report_template.xml",
    ],
    "installable": True,
    "application": False,
}
