# Copyright 2019 Darío Lodeiros, Alexandre Díaz, Jose Luis Algara, Pablo Quesada
# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Property Management System",
    "summary": "Manage properties",
    "version": "14.0.1.1.1",
    "development_status": "Beta",
    "category": "Generic Modules/Property Management System",
    "website": "https://github.com/OCA/pms",
    "author": "Commit [Sun], Open Source Integrators, Odoo Community Association (OCA)",
    "maintainers": ["max3903"],
    "license": "AGPL-3",
    "application": True,
    "depends": ["base_geolocalize", "mail", "product"],
    "data": [
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "data/pms_stage.xml",
        "data/pms_team.xml",
        "data/pms_amenity_type.xml",
        "data/pms_room_type.xml",
        "views/pms_tag.xml",
        "views/pms_stage.xml",
        "views/pms_amenity_type.xml",
        "views/pms_amenity.xml",
        "views/pms_room_type.xml",
        "views/pms_room.xml",
        "views/pms_service.xml",
        "views/pms_property.xml",
        "views/res_config_settings.xml",
        "views/pms_team.xml",
        "views/menu.xml",
        "views/res_partner_view.xml",
    ],
}
