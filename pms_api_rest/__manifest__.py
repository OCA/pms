{
    "name": "API REST PMS",
    "author": "Commit [Sun], Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/pms",
    "category": "Generic Modules/Property Management System",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "pms",
        "base_rest",
        "base_rest_datamodel",
        "web",
        "auth_signup",
        "auth_jwt_login",
        "base_location",
    ],
    "external_dependencies": {
        "python": ["jwt", "simplejson", "marshmallow", "jose"],
    },
    "data": [
        "data/auth_jwt_validator.xml",
        "views/pms_property_views.xml",
        "views/res_users_views.xml",
    ],
    "demo": [
        "demo/pms_api_rest_master_data.xml",
    ],
    "installable": True,
}
