# Copyright 2019 Darío Lodeiros, Alexandre Díaz, Jose Luis Algara, Pablo Quesada
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "PMS (Property Management System)",
    "summary": "A property management system",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "category": "Generic Modules/Property Management System",
    "website": "https://github.com/OCA/pms",
    "author": "Commit [Sun], Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": True,
    "installable": True,
    "depends": [
        "base",
        # "base_automation",
        "mail",
        # "sales_team",
        # "multi_pms_properties",
        # "partner_firstname",
        # "partner_second_lastname",
        # "partner_contact_gender",
        # "partner_contact_birthdate",
        # "partner_contact_nationality",
        # # "partner_identification_unique_by_category",
        # "queue_job",
        # "web_timeline",
        # "partner_identification",
        "account",
        # "sale",
    ],
    "data": [
        "security/pms_security.xml",
        "security/ir.model.access.csv",
        "views/menus.xml",
        # Master Data
        "views/pms_cancelation_rule_views.xml",
        "views/pms_property_views.xml",
        "views/pms_amenity_views.xml",
        "views/pms_amenity_type_views.xml",
        "views/pms_room_type_class_views.xml",
        "views/pms_room_type_views.xml",
        "views/pms_room_views.xml",
        "views/pms_ubication_views.xml",
        "views/pms_room_closure_reason_views.xml",
        "views/pms_board_service_views.xml",
        "views/pms_board_service_room_type_views.xml",
        # --
        "views/res_company_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "pms/static/src/js/payment_form.js",
        ],
    },
}
