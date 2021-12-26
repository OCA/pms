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
    ],
    "external_dependencies": {
        "python": ["jwt", "simplejson", "marshmallow"],
    },
    "data": [
        "security/ir.model.access.csv", "data/auth_jwt_validator.xml"
    ],
    "installable": True,
}
