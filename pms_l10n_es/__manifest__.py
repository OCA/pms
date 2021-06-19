# Copyright 2020 CommitSun (<http://www.commitsun.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "PMS Spanish Adaptation",
    "version": "14.0.2.0.0",
    "author": "Commit [Sun], Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": True,
    "category": "Localization",
    "website": "https://github.com/OCA/pms",
    "depends": [
        "pms",
        "partner_firstname",
        "partner_second_lastname",
        "partner_contact_gender",
        "partner_contact_birthdate",
        "partner_contact_nationality",
        "queue_job",
    ],
    "external_dependencies": {
        "python": [
            "bs4",
        ],
    },
    "data": [
        "data/cron_jobs.xml",
        "data/pms_data.xml",
        "data/queue_data.xml",
        "data/queue_job_function_data.xml",
        "security/ir.model.access.csv",
        "views/pms_property_views.xml",
        "views/pms_log_institution_traveller_report_views.xml",
        "wizards/traveller_report.xml",
    ],
    "installable": True,
}
