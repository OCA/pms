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
    ],
    "data": [
        # "wizard/housekeeping_rack.xml",
        "views/pms_room_view.xml",
        "views/pms_reservation_view.xml",
        "views/pms_housekeeping_task_view.xml",
        "views/pms_housekeeping_views.xml",
        "security/ir.model.access.csv",
        "data/cron_jobs.xml",
    ],
    "demo": [
        "demo/pms_housekeeping.xml",
    ],
    "installable": True,
}
