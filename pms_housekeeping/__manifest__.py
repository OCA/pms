# Copyright 2020-21 Jose Luis Algara (Alda Hotels <https://www.aldahotels.es>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Housekeeping",
    "version": "14.0.1.0.1",
    "author": "Commit [Sun], Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": True,
    "category": "pms",
    "website": "https://github.com/OCA/pms",
    "depends": [
        "pms",
        "hr",
        "pms_hr_property",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/pms_housekeeping_data.xml",
        "data/cron_jobs.xml",
        "views/hr_employee_views.xml",
        "views/pms_housekeeping_task_type_views.xml",
        "views/pms_housekeeping_views.xml",
        "views/pms_housekeeping_task_views.xml",
        "views/pms_room_views.xml",
    ],
    "installable": True,
}
