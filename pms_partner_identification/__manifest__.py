{
    "name": "PMS partner identification",
    "version": "16.0.2.1.0",
    "summary": "Add identification models in pms",
    "development_status": "Beta",
    "category": "Generic Modules/Property Management System",
    "website": "https://github.com/OCA/pms",
    "author": "Commit [Sun], Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "pms",
        "partner_identification",
    ],
    "external_dependencies": {
        "python": [
            "openupgradelib",
        ],
    },
    "data": [
        "views/pms_checkin_partner.xml",
        "views/res_partner_id_category.xml",
        "views/res_partner_id_number.xml",
        "data/res_partner_id_category.xml",
    ],
    "installable": True,
    "application": False,
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
}
