{
    "name": "PMS Noukee",
    "version": "14.0.1.0.1",
    "author": "Commit [Sun], Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": True,
    "category": "pms",
    "website": "https://github.com/OCA/pms",
    "depends": [
        "pms",
    ],
    "external_dependencies": {"python": ["requests"]},
    "data": [
        "views/pms_room_view.xml",
        "views/pms_door_views.xml",
        "views/pms_property_views.xml",
        "views/pms_reservation_view.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
